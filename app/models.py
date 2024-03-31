from app import db
from datetime import datetime
import pandas as pd
import json
from werkzeug.security import generate_password_hash,check_password_hash

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String,nullable=False,unique=True)
    password = db.Column(db.String,nullable=False)
    created_at = db.Column(db.DateTime,default=datetime.now())
    email = db.Column(db.String,nullable=False)

    def __init__(self,username,password,email):
        self.username = username
        password = generate_password_hash(password)
        self.password = password
        self.email = email
    
    def check_password(self,password):
        if check_password_hash(self.password,password):
            return True
        else:
            return False

    @property
    def get_info(self):
        return {'username':self.username,'email':self.email,'password':self.password,'create_at':self.created_at.strftime("%d %b %Y, %H:%M:%S")}

class Data(db.Model):
    __tablename__ = "data"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.now())
    data_path = db.Column(db.String, nullable=False, unique=True)
    created_by = db.Column(db.String, nullable=False)
    n_rows = db.Column(db.Integer, nullable=False)
    n_cols = db.Column(db.Integer, nullable=False)
    target = db.Column(db.String, nullable=False)  # dict
    feature = db.Column(db.String, nullable=False)
    labels = db.Column(db.Text)  # yang akan dilabelling oleh user : dict
    current_idx = db.Column(db.Integer, default=0)

    def __init__(self, data_path, created_by, feature, target, title=None):
        df = pd.read_csv(data_path)
        check_feature = False if not feature in df.columns.tolist() else True
        check_missing_value = False if sum(df.isna().sum().values) > 0 else True
        if check_feature and check_missing_value:
            shape = df.shape
            self.data_path = data_path
            self.created_by = created_by
            self.n_rows = shape[0]
            self.n_cols = shape[1]
            self.feature = feature
            self.target = json.dumps(target)
            self.labels = json.dumps({})
            self.title = title
        else:
            raise ValueError(f"Value Error ! {check_feature},{check_missing_value}")

    def read_data(self):
        df = pd.read_csv(self.data_path)
        return df

    def sample(self, n_sample: int):
        df = self.read_data()
        return df.sample(n_sample)

    def add_label(self, label):
        if label not in self.get_target:
            return {"msg": "label not in target"}, 404
        if self.current_idx == self.n_rows:
            return {"msg": "labelling is finished !"}, 404
        else:
            labels = json.loads(self.labels)
            labels[self.current_idx] = label
            self.labels = json.dumps(labels)
            self.current_idx += 1
            db.session.commit()
            return {"msg": "success"}, 200

    def edit_label(self, feature_id, label):
        if label not in self.get_target:
            return {"msg": "label not in target"}, 404
        labels = json.loads(self.labels)
        labels[int(feature_id)] = label
        self.labels = json.dumps(labels)
        db.session.commit()
        return {"msg": "success"}, 200

    @property
    def get_target(self):
        return json.loads(self.target)

    def get_info(self):
        return {
            "title": self.title,
            "created_by": self.created_by,
            "created_at": self.created_at.strftime("%d %b %Y"),
            "path": self.data_path,
            "feature": self.feature,
            "target": self.get_target,
            "shape": (self.n_rows, self.n_cols),
            "progress": f"{self.current_idx/self.n_rows*100:.2f}%",
        }

    @property
    def get_feature(self) -> dict:
        df = self.read_data()
        if self.current_idx == self.n_rows:
            return {"msg": "labelling is finished !"}, 404
        else:
            feature = df.loc[self.current_idx][self.feature]
            return {"target": self.get_target, "feature": feature}, 200

    @property
    def get_all_feature(self) -> dict:
        df = self.read_data()
        feature = df[self.feature].to_dict()
        labels = json.loads(self.labels)
        for i in labels:
            label = labels[i]
            text = feature[int(i)]
            labels[i] = {"text": text, "label": label}
        labels["target"] = self.get_target
        labels["progress"] = f"{self.current_idx/self.n_rows*100:.2f}%"
        labels["rest"] = self.n_rows - self.current_idx
        return labels

    def export_data(self):
        if self.n_rows != self.current_idx:
            return False
        df = self.read_data()
        labels = json.loads(self.labels).values()
        df["labels"] = labels
        df.to_csv(self.data_path, index=False)
        return self.data_path

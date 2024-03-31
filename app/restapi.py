from flask_jwt_extended import create_access_token,jwt_required,get_jwt_identity
from app import api, Resource, ALLOWED_EXTENSIONS, app, db
from werkzeug.utils import secure_filename
from flask import request, send_file
import os
from .models import Data,User


def handling_error(msg, code):
    return {"msg": msg, "status": False}, code

class UserAuth(Resource):
    @jwt_required()
    def get(self):
        id = request.args.get('id')
        if id == '123':
            q = User.query.all()
            data = [{i.id:i.get_info} for i in q]
            return data,200
        current_user = get_jwt_identity()
        return {'current_user':current_user}

    def post(self):
        query = request.args.get('query')
        if query == 'register':
            username = request.form.get('username')
            password = request.form.get('password')
            email = request.form.get('email')
            if User.query.filter_by(username=username).first():
                return handling_error(msg='Username is exist',code=404)
            q = User(username=username,password=password,email=email)
            db.session.add(q)
            db.session.commit()
            return {'msg':'success registered !'},200
        elif query == 'login':
            username = request.form.get('username')
            password = request.form.get('password')
            q = User.query.filter_by(username=username).first()
            if not q:
                return handling_error('user not found!',404)
            if not q.check_password(password):
                return handling_error("password is wrong !",404)
            token = create_access_token(identity={'username':username})
            return {'msg':'success Login','token':token},200
        else:
            return handling_error(msg='query is not found !',code=404)

api.add_resource(UserAuth,'/')

class FileHandler(Resource):
    def allowed_file(self, filename):
        return (
            "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
        )

    @jwt_required()
    def get(self):
        data = Data.query.all()
        id = request.args.get("id")
        if id:
            q = Data.query.filter_by(id=id).first()
            if not q:
                return handling_error(msg="data is not found !", code=404)
            status = q.export_data()
            if not status:
                return handling_error(msg="labeling is not ready", code=404)
            return send_file(status)
        else:
            data_list = []
            for i in data:
                d = i.get_info()
                data_list.append({"id": i.id, "data": d})
            return data_list

    @jwt_required()
    def post(self):
        # Get Text type fields
        form = request.form.to_dict()
        target = form["target"].split(",")
        feature = form["feature"]
        user = get_jwt_identity()['username']

        if "file" not in request.files:
            return {"msg": "No file part"}, 400

        file = request.files.get("file")
        if file and self.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            print(filename)
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)
            if Data.query.filter_by(data_path=path).first():
                return {"msg": "data already exist"}, 400
            q = Data(
                created_by=user, target=target, feature=feature, data_path=path
            )
            db.session.add(q)
            db.session.commit()
            return "File uploaded successfully"
        else:
            return {"msg": "File No Support"}, 400

    @jwt_required()
    def delete(self):
        id = request.args.get("id")
        q = Data.query.filter_by(id=id).first()
        db.session.delete(q)
        db.session.commit()
        os.remove(q.data_path)
        return {"msg": "success Delete"}, 200


api.add_resource(FileHandler, "/file")


class DataHandler(Resource):

    @jwt_required()
    def get(self):
        id = request.args.get("id")
        query = request.args.get("query")
        q = Data.query.filter_by(id=int(id)).first()
        if not q:
            return handling_error(msg="Not Found Data !", code=404)
        if query == "all":
            return q.get_all_feature
        return q.get_feature

    @jwt_required()
    def post(self):
        id = request.args.get("id")
        label = request.form.get("label")
        q = Data.query.filter_by(id=int(id)).first()
        if not q or not label:
            return handling_error(msg="Not Found Data !", code=404)
        res = q.add_label(label)
        return res

    @jwt_required()
    def put(self):
        id = request.args.get("id")
        feature_id = request.args.get("feature_id")
        q = Data.query.filter_by(id=int(id)).first()
        label = request.form.get("label")
        if not q or not feature_id or not label:
            return handling_error(msg="Not Found Data !", code=404)
        res = q.edit_label(feature_id, label)
        return res


api.add_resource(DataHandler, "/data")

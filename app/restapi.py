from flask_jwt_extended import create_access_token
from app import api,Resource,ALLOWED_EXTENSIONS,app,db
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash,check_password_hash
from flask import request,send_file
import os
from .models import Data

def handling_error(msg,code):
    return {'msg':msg,'status':False},code



class FileHandler(Resource):
    def allowed_file(self,filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def get(self):
        data = Data.query.all()
        id = request.args.get('id')
        if id:
            q = Data.query.filter_by(id=id).first()
            if not q:
                return handling_error(msg='data is not found !',code=404)
            status = q.export_data()
            if not status:
                return handling_error(msg='labeling is not ready',code=404)
            return send_file(status)
        else:
            data_list = []
            for i in data:
                d = i.get_info()
                data_list.append({'id':i.id,'data':d})
            return data_list

    def post(self):
        # Get Text type fields
        form = request.form.to_dict()
        target = form['target'].split(',')
        feature = form['feature']
        created_by = form['created_by']

        if 'file' not in request.files:
            return {'msg':'No file part'},400

        file = request.files.get("file")
        if file and self.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            print(filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            if Data.query.filter_by(data_path=path).first():
                return {'msg':'data already exist'},400
            q = Data(created_by=created_by,target=target,feature=feature,data_path=path)
            db.session.add(q)
            db.session.commit()
            return 'File uploaded successfully'
        else:
            return {'msg':'File No Support'},400

    def delete(self):
        id = request.args.get('id')
        q = Data.query.filter_by(id=id).first()
        db.session.delete(q)
        db.session.commit()
        os.remove(q.data_path)
        return {'msg':'success Delete'},200

api.add_resource(FileHandler, "/file")

class DataHandler(Resource):

    def get(self):
        id = request.args.get('id')
        query = request.args.get('query')
        q = Data.query.filter_by(id=int(id)).first()
        if not q:
            return handling_error(msg='Not Found Data !',code=404)
        if query == "all":
            return q.get_all_feature
        return q.get_feature
    
    def post(self):
        id = request.args.get('id')
        label = request.form.get('label')
        q = Data.query.filter_by(id=int(id)).first()
        if not q or not label:
            return handling_error(msg='Not Found Data !',code=404)
        res = q.add_label(label)
        return res
    
    def put(self):
        id = request.args.get('id')
        feature_id = request.args.get('feature_id')
        q = Data.query.filter_by(id=int(id)).first()
        label = request.form.get('label')
        if not q or not feature_id or not label:
            return handling_error(msg='Not Found Data !',code=404)
        res = q.edit_label(feature_id,label)
        return res
        

api.add_resource(DataHandler,"/data")

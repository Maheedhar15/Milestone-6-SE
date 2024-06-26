from flask_restful import Resource, request, abort
from flask import jsonify
from datetime import datetime
from dateutil import tz, parser
from application.models import User, Response, Ticket, FAQ, Category, Flagged_Post, DiscoursePost
from application.models import token_required, db
from application.workers import celery
from celery import chain
from application.tasks import send_email, response_notification
from datetime import datetime, timedelta
import jwt
from .config import Config, LocalDevelopmentConfig
from werkzeug.exceptions import HTTPException
from application import index
import requests
import json

class TicketAPI(Resource):
    @token_required
    def get(user,self):
        if(user.role_id==1):
            ticket=Ticket.query.filter_by(creator_id=user.user_id).all()
            result=[]
            for t in ticket:
                d={}
                d['ticket_id']=t.ticket_id
                d['title']=t.title
                d['description']=t.description
                d['creation_date']=str(t.creation_date)
                d['creator_id']=t.creator_id
                d['number_of_upvotes']=t.number_of_upvotes
                d['is_read']=t.is_read
                d['is_open']=t.is_open
                d['is_offensive']=t.is_offensive
                d['is_FAQ']=t.is_FAQ
                d['rating']=t.rating
                result.append(d)
            return jsonify({"data": result})
        else:
            abort(403,message="You are not authorized to view this page")
    @token_required
    def post(user,self):
        if(user.role_id==1):
            data=request.get_json()
            ticket=Ticket(title=data['title'],
                          description=data['description'],
                          creation_date=datetime.now(),
                          creator_id=user.user_id,
                          number_of_upvotes=data['number_of_upvotes'],
                          is_read=data['is_read'],
                          is_open=data['is_open'],
                          is_offensive=data['is_offensive'],
                          is_FAQ=data['is_FAQ'])
            db.session.add(ticket)
            db.session.commit()
            tk_obj = {
                'objectID': ticket.ticket_id,
                'ticket_id': ticket.ticket_id,
                'title': ticket.title,
                'description': ticket.description,
                'creation_date': ticket.creation_date,
                'creator_id': ticket.creator_id,
                'number_of_upvotes': ticket.number_of_upvotes,
                'is_read': ticket.is_read,
                'is_offensive': ticket.is_offensive,
                'is_FAQ': ticket.is_FAQ,
                'rating': ticket.rating,
                'responses': []
            }
            index.save_object(obj=tk_obj)
            return jsonify({'message':'Ticket created successfully'})
        else:
            abort(403,message="You are not authorized to view this page")
        
    @token_required
    def patch(user, self):
        if user.role_id==1:
            args = request.get_json(force = True)
            a = None
            try:
                a = int(args["ticket_id"])
                #print(a)
                #print(user.user_id)
            except:
                abort(400, message = "Please mention the ticketId field in your form")
            ticket = None
            try:
                ticket = Ticket.query.filter_by(ticket_id = a, creator_id = user.user_id).first()
            except:
                abort(404, message = "There is no such ticket by that ID")
            title = None
            try:
                title = args["title"]
                ticket.title = title
            except:
                pass
            description = None
            try:
                description = args["description"]
                ticket.description = description
            except:
                pass
            number_of_upvotes = None

            try:
                number_of_upvotes = int(args["number_of_upvotes"])
                ticket.number_of_upvotes = number_of_upvotes
            except:
                pass
            is_read = None
            try:
                if args["is_read"] is not None:
                    is_read = args["is_read"]
                    ticket.is_read = is_read
            except:
                pass
            is_open = None
            try:
                if args["is_open"] is not None:
                    is_open = args["is_open"]
                    ticket.is_open = is_open
            except:
                pass
            is_offensive = None
            try:
                if args["is_offensive"] is not None:
                    is_offensive = args["is_offensive"]
                    ticket.is_offensive = is_offensive
            except:
                pass
            is_FAQ = None
            try:
                if args["is_FAQ"] is not None:
                    is_FAQ = args["is_FAQ"]
                    ticket.is_FAQ = is_FAQ
            except:
                pass 
            try:
                rating =  args["rating"]
                ticket.rating = rating
                #print("I am here!")
            except:
                pass  
            db.session.commit()
            tk_obj = {
                'objectID': ticket.ticket_id,
                'ticket_id': ticket.ticket_id,
                'title': ticket.title,
                'description': ticket.description,
                'creation_date': ticket.creation_date,
                'creator_id': ticket.creator_id,
                'number_of_upvotes': ticket.number_of_upvotes,
                'is_read': ticket.is_read,
                'is_offensive': ticket.is_offensive,
                'is_FAQ': ticket.is_FAQ,
                'rating': ticket.rating,
                'responses': [resp.response for resp in ticket.responses]
            }
            index.partial_update_object(obj=tk_obj)
            try:
          
                post_id = ticket.discourse_post_id
                print(post_id)
                url = 'http://localhost:4200/posts/'+str(post_id)
                print(url)
                data={
                    "post":{
                        "raw":ticket.description,
                        "edit_reason":"Update post"
                    }
                }
                headers = {
                        "Api-Key": LocalDevelopmentConfig.DISCOURSE_API_KEY,
                        "Api-Username": user.discourse_username
                        }
               
                # 'id': 62, 'name': 'studen1', 'username': 'studen1', 'avatar_template': '/letter_avatar_proxy/v4/letter/s/ecae2f/{size}.png', 'created_at': '2024-04-19T13:41:18.178Z', 'cooked': '<p>hola everyone edfasda 2232sdasd</p>', 'post_number': 1, 'post_type': 1, 'updated_at': '2024-04-19T14:27:39.672Z', 'reply_count': 0, 'reply_to_post_number': None, 'quote_count': 0, 'incoming_link_count': 0, 'reads': 1, 'readers_count': 0, 'score': 0.2, 'yours': True, 'topic_id': 60, 'topic_slug': 'das-dasdasd-asd-adasdasd-asd', 'display_username': 'studen1', 'primary_group_name': None, 'flair_name': None, 'flair_url': None, 'flair_bg_color': None, 'flair_color': None, 'flair_group_id': None, 'version': 2, 'can_edit': True, 'can_delete': False, 'can_recover': False, 'can_see_hidden_post': True, 'can_wiki': False, 'user_title': None, 'bookmarked': False, 'raw': 'hola everyone edfasda 2232sdasd', 'actions_summary': [{'id': 3, 'can_act': True}, {'id': 4, 'can_act': True}, {'id': 8, 'can_act': True}, {'id': 7, 'can_act': True}, {'id': 10, 'can_act': True}], 'moderator': False, 'admin': False, 'staff': False, 'user_id': 36, 'draft_sequence': 2, 'hidden': False, 'trust_level': 1, 'deleted_at': None, 'user_deleted': False, 'edit_reason': 'Update post', 'can_view_edit_history': True, 'wiki': False}}
                request1 = requests.put(url, json = data, headers = headers) 
                print(request1.status_code)
                # print(request1.content)        
                if request1.status_code == 200:
                    resp = request1.json()
                    print(resp)
                    discourse = DiscoursePost.query.filter_by(post_id = post_id).first()
                    discourse.raw = ticket.description
                    discourse.post_number = resp['post_number']
                    discourse.post_type = resp['post_type']
                    discourse.updated_at = resp['updated_at']
                    discourse.reply_count = resp['reply_count']
                    discourse.reply_to_post_number = resp['reply_to_post_number']
                    discourse.quote_count = resp['quote_count']
                    discourse.incoming_link_count = resp['incoming_link_count']
                    discourse.reads = resp['reads']
                    discourse.readers_count = resp['readers_count']
                    discourse.score = resp['score']
                    discourse.yours = resp['yours']
                    discourse.topic_id = resp['topic_id']
                    discourse.topic_slug = resp['topic_slug']
                    discourse.display_username = resp['display_username']
                    discourse.primary_group_name = resp['primary_group_name']
                    discourse.version = resp['version']
                    discourse.can_edit = resp['can_edit']
                    discourse.can_delete = resp['can_delete']
                    discourse.can_recover = resp['can_recover']
                    discourse.can_see_hidden_post = resp['can_see_hidden_post']
                    discourse.can_wiki = resp['can_wiki']
                    discourse.user_title = resp['user_title']
                    discourse.bookmarked = resp['bookmarked']
                    discourse.raw = resp['raw']
                    
                    
                    db.session.commit()
                    return jsonify({"message": "Ticket updated successfully"})
            except:
                pass
            return jsonify({"message": "Ticket updated successfully"})
        
        else:
            abort(403,message= "You are not authorized to access this!")
            


class TicketDelete(Resource):
    @token_required
    def delete(user,self,ticket_id):
        current_ticket = db.session.query(Ticket).filter(Ticket.ticket_id==ticket_id,Ticket.creator_id==user.user_id).first()
        if current_ticket:
            responses = db.session.query(Response).filter(Response.ticket_id==ticket_id).all()
            if responses:
                for post in responses:
                    db.session.delete(post)
                    db.session.commit() 
            db.session.delete(current_ticket)
            db.session.commit()
            index.delete_object(current_ticket.ticket_id)
            try:
                post_id = current_ticket.discourse_post_id
                print(post_id)
                url = 'http://localhost:4200/posts/'+str(post_id)
                print(url)
                data={
                    "force_destroy": "true"
                }
                headers = {
                        "Api-Key": LocalDevelopmentConfig.DISCOURSE_API_KEY,
                        "Api-Username": user.discourse_username
                }
                request1 = requests.put(url, json = data, headers = headers) 
                print(request1.status_code)
                # print(request1.content)        
                if request1.status_code == 200:
                    resp = request1.json()
                    print(resp)
                    return jsonify({"message": "Ticket deleted successfully"})
                
            except:
                pass
            
            
            return jsonify({"message": "Ticket deleted successfully"})
        else:
            abort(400, message='No such ticket_id exists for the user')

import secrets,string    
from random_username.generate import generate_username   

class UserAPI(Resource):
    @token_required
    def get(user,self):
        if(user.role_id==3):
            user=User.query.all()
            result=[]
            for user in user:
                if(user.role_id==1 or user.role_id==2):
                    d={}
                    d['user_id']=user.user_id
                    d['user_name']=user.user_name
                    d['email_id']=user.email_id
                    d['role_id']=user.role_id
                    result.append(d)
            return jsonify({"data": result})
        else:
            abort(403,message="You are not authorized to view this page")
    @token_required
    def post(user,self):
        if(user.role_id==3 or user.role_id==4):
            data=request.get_json()
            print(data)
            data = json.loads(data['data'])
            secure_str = data['password']
            user_name= data['username']
            user=User(user_name=user_name,email_id=data["email_id"],password=secure_str,role_id=data['role_id'])
            db.session.add(user)
            db.session.commit()
            return jsonify({'message':'User created successfully'})
        else:
            abort(403,message="You are not authorized to view this page")
            
    @token_required
    def patch(user,self):
        args=request.get_json(force=True)
        user_id=None
        current_user=None
        try:
            user_id=int(args['user_id'])
        except:
            abort(400,message="user_id must exist and should be integer")
        try:
            current_user=User.query.filter(User.user_id==user_id).first()
        except:
            abort(400,message="No such user_id exists")
        user_name=None
        try:
            user_name=args['user_name']
            current_user.user_name=user_name
        except:
            pass
        try:
            password=args['password']
            current_user.password=password
        except:
            pass
        try:
            email_id=args['email_id']
            if(user.role_id==3):
                current_user.email_id=email_id
            else:
                abort(403,message="You are can't edit email")
        except:
            pass
        db.session.commit()
        return jsonify({'message':'User updated successfully'})
    
class UserDelete(Resource):
    @token_required
    def delete(user,self,user_name):
        if user.role_id==3:
            current_user = User.query.filter(User.user_name==user_name).first()
            if current_user:
                data1 = {
                        "delete_posts": "true",
                        "block_email": "true",
                        "block_urls": "true",
                        "block_ip": "true"
                }
                headers = {
                    "Api-Key": "e5299d207efeb7e5c2eb544877eb60c9574ca0b515019f7372bf6136a1cb95b9",
                    "Api-Username": "maheedhareducation"
                }
                url = f"http://localhost:4200/admin/users/{current_user.discourse_userid}"
                requ = requests.delete(url,json=data1, headers = headers)
                print(requ) 
                print("Response status code:", requ.status_code)
                print("Response content:", requ.content)
                db.session.delete(current_user)
                db.session.commit()
                return jsonify({'message':'User deleted successfully'})
            else:
                abort(400, 'No such user_id exists')
        else:
            abort(403, message="Unauthorized")

class FAQApi(Resource):
    @token_required
    def get(user,self):
        faq = db.session.query(FAQ).all()
        result = []
        for q in faq:
            d = {}
            d['ticket_id'] = q.ticket_id
            d['category'] = q.category
            d['is_approved'] = q.is_approved
            d['title'] = q.ticket.title
            d['description'] = q.ticket.description
            d['creation_date'] = q.ticket.creation_date
            d['creator_id'] = q.ticket.creator_id
            d['number_of_upvotes'] = q.ticket.number_of_upvotes
            d['is_read'] = q.ticket.is_read
            d['is_open'] = q.ticket.is_open
            d['is_offensive'] = q.ticket.is_offensive
            d['is_FAQ'] = q.ticket.is_FAQ
            d['rating'] = q.ticket.rating
            result.append(d)
        return jsonify({"data": result})

    @token_required
    def post(user, self):
        if user.role_id == 3:
            data = request.get_json()
            try:
                tid = int(data['ticket_id'])
            except:
                abort(400, message="ticket_id is required and should be integer")
            try:
                is_app = data['is_approved']
            except:
                abort(400, message="is_approved is required and should be boolean")
            
            if is_app: 
                try:
                    cat = data['category']
                except:
                    abort(400, message="category is required and should be string")
            else:
                cat = None

            if not db.session.query(Ticket).filter(Ticket.ticket_id==tid).first():
                abort(400, message="ticket_id does not exist")

            if cat is not None and db.session.query(Category).filter(Category.category==cat).first() is None:
                abort(400, message="category does not exist")

            if not isinstance(is_app, bool):
                abort(400, message="is_approved must be boolean")
            
            if db.session.query(FAQ).filter(FAQ.ticket_id== tid).first():
                abort(400, message="ticket already in FAQ")

            newFAQ = FAQ(ticket_id = tid, category=cat, is_approved=is_app)
            db.session.add(newFAQ)
            db.session.commit()  

            return jsonify({'message': "FAQ item added successfully"})               

        else:
            abort(403, message="Unauthorized")
    
    @token_required
    def patch(user, self):
        if user.role_id==3:
            data = request.get_json()
            try:
                tid = int(data['ticket_id'])
            except:
                abort(400, message="ticket_id is required and should be integer")
            
            if not db.session.query(Ticket).filter(Ticket.ticket_id==tid).first():
                    abort(400, message="ticket_id does not exist")
            current_ticket=db.session.query(FAQ).filter(FAQ.ticket_id==tid).first()
            if not current_ticket: 
                abort(400, message="ticket_id is not in FAQ")
            cat = None
            try:
                cat = data['category']
                if not db.session.query(Category).filter(Category.category==cat).first():
                    abort(400, message="category does not exist")
                else:
                    current_ticket.category = cat
            except Exception as e:
               if isinstance(e, HTTPException):
                   raise e
            try:
                is_app = data['is_approved']
                if not isinstance(is_app, bool):
                    abort(400, message="is_approved must be boolean")
                else:
                    current_ticket.is_approved = is_app
            except Exception as e:
               if isinstance(e, HTTPException):
                   raise e
                 
            db.session.commit()
            return jsonify({'message': "FAQ item updated successfully"})
                
        else:
            abort(403, message="Unauthorized")
    
    @token_required
    def delete(user, self, ticket_id):
        if user.role_id==3:
            tid = ticket_id
            
            if not db.session.query(Ticket).filter(Ticket.ticket_id==tid).first():
                abort(400, message="ticket_id does not exist")
            
            current_ticket=db.session.query(FAQ).filter(FAQ.ticket_id==tid).first()
            if current_ticket:
                db.session.delete(current_ticket)
                db.session.commit()
                return jsonify({'message': "FAQ item deleted successfully"})
            else:
                abort(400, message="ticket_id is not in FAQ")
        else:
            abort(403, message="Unauthorized")
        
class getResponseAPI_by_ticket(Resource):
     @token_required
     def post(user, self):
        responses = None
        ticket_id = None
        args = request.get_json(force = True)
        try:
            ticket_id = int(args["ticket_id"])
        except:
            abort(403,message = "Please provide a ticket ID for which you need the responses.")
        
        try:
            responses = Response.query.filter_by(ticket_id = ticket_id).all()
        except:
            abort(404, message= "There are no tickets by that ID.")
        
        responses = list(responses)
        l = []
        for item in responses:
            d = {}
            d["response_id"] = item.response_id
            d["ticket_id"] = item.ticket_id
            d["response"] = item.response
            d["responder_id"] = item.responder_id
            d["response_timestamp"] = item.response_timestamp
            l.append(d)
        return jsonify({"data": l, "status": "success"})
     
class ResponseAPI_by_ticket(Resource):
    @token_required
    def post(user, self):
        if user.role_id == 1 or user.role_id == 2:
            args = request.get_json(force = True)
            ticket_id = None
            try:
                ticket_id = args["ticket_id"]
            except:
                abort(403, message = "Please provide the ticket id!")
            response = None
            try:
                response = args["response"]
            except:
                abort(403, message = "Please add your response!")
            responder_id = user.user_id
            ticket_obj = Ticket.query.filter_by(ticket_id = ticket_id).first()
            if ticket_obj:
                response_obj = Response(ticket_id = ticket_id, response = response, responder_id = responder_id)
                db.session.add(response_obj)
                db.session.commit()
                index.partial_update_object({
                    'responses': {
                        '_operation': 'Add',
                        'value': response_obj.response
                    },
                    'objectID': ticket_obj.ticket_id
                })
                if user.role_id == 2 or (user.role_id==1 and user.user_id != ticket_obj.creator_id):
                    tk = {'title': ticket_obj.title, 'ticket_id': ticket_obj.ticket_id, 'creator_id': ticket_obj.creator_id, 'creator_email': ticket_obj.creator.email_id}
                    rp = {'responder_id': response_obj.responder_id, 'response': response_obj.response, 'response_id': response_obj.response_id, 'responder_uname': response_obj.responder.user_name}
                    send_notification = chain(response_notification.s(ticket_obj = tk, response_obj=rp), send_email.s()).apply_async()
                return jsonify({"status": "success"})
            else:
                abort(404, message =
                       "This ticket doesn't exist.")
            

        else:
            abort(404, message = "You are not authorized to post responses to a ticket.")

    @token_required
    def patch(user, self):
        #Allows only to change the response 
        #All other operations, like changing the ticket id, etc is not allowed.

        if user.role_id == 1 or user.role_id == 2:
            args = request.get_json(force = True)
            response = None
            response_id = None
            responder_id = user.user_id
            try:
                response_id = args["response_id"]
            except:
                abort(404, message = "Please provide the response id")
            try:
                response = args["response"]
            except:
                abort(404, message = "Since your update response was blank, your earlier response hasn't been altered.")
            response_obj = Response.query.filter_by(responder_id = responder_id, response_id = response_id).first()
            if response_obj:
                index.partial_update_object({
                    'responses': {
                        '_operation': 'Remove',
                        'value': response_obj.response
                    },
                    'objectID': response_obj.ticket_id
                })
                response_obj.response = response
                db.session.commit()
                index.partial_update_object({
                    'responses': {
                        '_operation': 'Add',
                        'value': response_obj.response
                    },
                    'objectID': response_obj.ticket_id
                })
                return jsonify({"status": "success"})
            else:
                abort(404, message = "Either your response id is wrong, or this account is not the responder of the particular response.")
        else:
            abort(404, message = "You are not authorized to update any responses.")

class ResponseAPI_by_responseID_delete(Resource):
    @token_required
    def delete(user, self, responder_id, response_id):
        if user.role_id ==1 or user.role_id == 2 or user.role_id == 3:
            responder_id_local = None
            responder_id_2 = responder_id
            if responder_id_2 and user.role_id == 3: #Admins can delete responses made by student/staff if they wish to.
                responder_id_local = responder_id_2
            else:
                responder_id_local = user.user_id
            response_obj = Response.query.filter_by(response_id = response_id, responder_id = responder_id_local).first()
            if response_obj:
                db.session.delete(response_obj)
                db.session.commit()
                index.partial_update_object({
                    'responses': {
                        '_operation': 'Remove',
                        'value': response_obj.response
                    },
                    'objectID': response_obj.ticket_id
                })
                return jsonify({"status": "success"})
            else:
                abort(404, message = "Either the response you are trying to delete is not yours, or the response doesn't exist in the first place.")

        else:
            abort(404, message = "You are not authorized to delete responses.")

class ResponseAPI_by_user(Resource):
    @token_required
    def post(user, self):
        if user.role_id == 4: #Only managers can do this. 
            responses = None
            responder_id = None
            args = request.get_json(force = True)
            try:
                responder_id= int(args["responder_id"])
            except:
                abort(403,message = "Please provide a responder ID for which you need the responses.")
            
            try:
                responses = Response.query.filter_by(responder_id = responder_id).all()
            except:
                abort(404, message= "There are no responses by that particular responder ID.")
            
            responses = list(responses)
            l = []
            for item in responses:
                d = {}
                d["response_id"] = item.response_id
                d["ticket_id"] = item.ticket_id
                d["response"] = item.response
                d["responder_id"] = item.responder_id
                d["response_timestamp"] = item.response_timestamp
                l.append(d)
            return jsonify({"data": l, "status": "success"})
        else:
            abort(404, message = "Sorry, you don't have access to this feature!")

class ResponseAPI_by_response_id(Resource): #This class can be used if required.
    @token_required
    def post(user, self):
        responses = None
        response_id = None
        args = request.get_json(force = True)
        try:
            response_id = int(args["response_id"])
        except:
            abort(403,message = "Please provide a response ID.")
        
        try:
            responses = Response.query.filter_by(response_id = response_id).first()
        except:
            abort(404, message= "There are no tickets by that ID.")
        if responses:
                d = {}
                d["response_id"] = responses.response_id
                d["ticket_id"] = responses.ticket_id
                d["response"] = responses.response
                d["responder_id"] = responses.responder_id
                d["response_timestamp"] = responses.response_timestamp
                return jsonify({"data": d, "status": "success"})
        else:
            return jsonify({"data": [], "status": "succcess"})

class TicketAll(Resource):
    @token_required
    def get(user,self):
        try:
            ticket=Ticket.query.all()
            result=[]
            for t in ticket:
                d={}
                d['ticket_id']=t.ticket_id
                d['title']=t.title
                d['description']=t.description
                d['creation_date']=str(t.creation_date)
                d['creator_id']=t.creator_id
                d['number_of_upvotes']=t.number_of_upvotes
                d['is_read']=t.is_read
                d['is_open']=t.is_open
                d['is_offensive']=t.is_offensive
                d['is_FAQ']=t.is_FAQ
                d['rating']=t.rating
                result.append(d)
            return jsonify({"data":result,"status":"success"})
        except:
            abort(404,message="No tickets found")
    
    @token_required
    def patch(user, self):
            args = request.get_json(force = True)
            a = None
            try:
                a = int(args["ticket_id"])
                #print(a)
                #print(user.user_id)
            except:
                abort(403, message = "Please mention the ticketId field in your form")
            ticket = None
            try:
                ticket = Ticket.query.filter_by(ticket_id = a).first()
                if ticket is None:
                    raise ValueError
            except:
                abort(404, message = "There is no such ticket by that ID")
            title = None
            try:
                title = args["title"]
                ticket.title = title
            except:
                pass
            description = None
            try:
                description = args["description"]
                ticket.description = description
            except:
                pass
            number_of_upvotes = None

            try:
                number_of_upvotes = int(args["number_of_upvotes"])
                ticket.number_of_upvotes = number_of_upvotes
            except:
                pass
            is_read = None
            try:
                if args["is_read"] is not None:
                    is_read = args["is_read"]
                    ticket.is_read = is_read
            except:
                pass
            is_open = None
            try:
                if args["is_open"] is not None:
                    is_open = args["is_open"]
                    ticket.is_open = is_open
            except:
                pass
            is_offensive = None
            try:
                if args["is_offensive"] is not None:
                    is_offensive = args["is_offensive"]
                    ticket.is_offensive = is_offensive
            except:
                pass
            is_FAQ = None
            try:
                if args["is_FAQ"] is not None:
                    is_FAQ = args["is_FAQ"]
                    ticket.is_FAQ = is_FAQ
            except:
                pass   
            rating = None
            try:
                rating =  args["rating"]
                ticket.rating = rating
                #print("I am here!")
            except:
                pass
            db.session.commit()
            return jsonify({"message": "success"})

class getResolutionTimes(Resource):
    #API to get resolution times.
    #Supports getting resolution times of a single ticket or multiple tickets all at once.
    @token_required
    def post(user, self):
        if user.role_id == 4:
            args = request.get_json(force = True)
            creation_time = None
            solution_time = None
            ticket_id = None
            try:
                ticket_id = args["ticket_id"]
                #print(ticket_id)
            except:
                abort(403, message = "Please enter the ticket ID.")
            if isinstance(ticket_id, list):
                data = []        
                for item in ticket_id:
                    d = {}
                    ticket = None
                    try:
                        ticket = Ticket.query.filter_by(ticket_id = item).first()
                        if ticket is None:
                            continue
                    except:
                        abort(404, message = "No such ticket exists by the given ticket ID.")
                    if isinstance(ticket.creation_date, str):
                        d["creation_time"] = datetime.strptime(ticket.creation_date, '%Y-%m-%d %H:%M:%S.%f')
                    elif isinstance(ticket.creation_date, datetime):
                        d["creation_time"] = ticket.creation_date
                    else:
                        abort(403, message = "The ticket object timestamp isn't in either string or datetime format.")
                    responses = Response.query.filter_by(ticket_id = item).all()
                    try:
                        if ticket.is_open == False:
                            responses = list(responses)
                            response_times = []
                            for thing in responses:
                                if isinstance(thing.response_timestamp, datetime):
                                    #print("Here 1")
                                    response_times.append(thing.response_timestamp)
                                elif isinstance(thing.response_timestamp, str):
                                    #print("Here 2")
                                    response_times.append(datetime.strptime(thing.response_timestamp,'%Y-%m-%d %H:%M:%S.%f'))
                                else:
                                    abort(403, message = "The response object timestamp isn't in either string or datetime format.")
                            response_time = max(response_times)
                            d["response_time"] = response_time
                            d["resolution_time_datetime_format"] = d["response_time"] - d["creation_time"]
                            d["days"] = d["resolution_time_datetime_format"].days
                            d["seconds"] = d["resolution_time_datetime_format"].seconds
                            d["microseconds"] = d["resolution_time_datetime_format"].microseconds
                            d["response_time"] = d["response_time"]
                            d["resolution_time_datetime_format"] = str(d["resolution_time_datetime_format"])
                            d["creation_time"] = d["creation_time"]
                            d["ticket_id"] = item
                            data.append(d)
                        else:
                            raise ValueError
                    except:
                        continue
                return jsonify({"data": data, "status": "success"})
            elif isinstance(ticket_id, int):
                #print("Here")
                d = {}
                try:
                    ticket = Ticket.query.filter_by(ticket_id = ticket_id).first()
                    if ticket is None:
                        raise ValueError
                except:
                    abort(404, message = "No such ticket exists by the given ticket ID.")
                if isinstance(ticket.creation_date, str):
                    d["creation_time"] = datetime.strptime(ticket.creation_date, '%Y-%m-%d %H:%M:%S.%f')
                elif isinstance(ticket.creation_date, datetime):
                    d["creation_time"] = ticket.creation_date
                else:
                    abort(403, message = "The ticket object timestamp isn't in either string or datetime format.")
                responses = Response.query.filter_by(ticket_id = ticket_id).all()
                try:
                    #print("Inside try")
                    if ticket.is_open == False:
                        print("Here")
                        responses = list(responses)
                        response_times = []
                        for thing in responses:
                            if isinstance(thing.response_timestamp, datetime):
                                #print("Here 1")
                                response_times.append(thing.response_timestamp)
                            elif isinstance(thing.response_timestamp, str):
                                #print("Here 2")
                                response_times.append(datetime.strptime(thing.response_timestamp,'%Y-%m-%d %H:%M:%S.%f'))
                            else:
                                abort(403, message = "The response object timestamp isn't in either string or datetime format.")
                        #print("Here3")
                        #print(response_times)
                        response_time = max(response_times)
                        d["response_time"] = response_time
                        d["resolution_time_datetime_format"] = d["response_time"] - d["creation_time"]
                        d["days"] = d["resolution_time_datetime_format"].days
                        d["seconds"] = d["resolution_time_datetime_format"].seconds
                        d["microseconds"] = d["resolution_time_datetime_format"].microseconds
                        d["response_time"] = d["response_time"]
                        d["resolution_time_datetime_format"] = str(d["resolution_time_datetime_format"])
                        d["creation_time"] = d["creation_time"]
                        d["ticket_id"] = ticket_id
                        return jsonify({"data": d, "status": "success"})
                    else:
                        abort(403, message = "This ticket has not been closed yet.")
                except:
                    abort(404, message = "This ticket hasn't been responded to yet or is still open!")
        else:
            return abort(404, message = "You are not authorized to access this feature!")

class invalidFlaggerException(Exception):
    pass

class invalidTicketException(Exception):
    pass

class invalidCreatorException(Exception):
    pass

class flaggedPostAPI(Resource):
    #Only admins can view all the flagged posts.
    @token_required
    def get(user,self):
        if user.role_id == 3:
            l = []
            flagged_posts = Flagged_Post.query.filter_by().all()
            if flagged_posts is not None:
                flagged_posts = list(flagged_posts)
                for item in flagged_posts:
                    if ((item.is_approved) and (not item.is_rejected))or ((not (item.is_approved)) and (not item.is_rejected)):
                        d = {}
                        d["ticket_id"] = item.ticket_id
                        d["flagger_id"] = item.flagger_id
                        d["creator_id"] = item.creator_id
                        d["is_approved"] = item.is_approved
                        d["is_rejected"] = item.is_rejected
                        l.append(d)
                return jsonify({"data": l, "status": "success"})
            else:
                return jsonify({"data": l, "status" : "success"})
        else:
            abort(404, message = "You are not authorized to access this feature.")
    
    @token_required
    #Only support agents can add a new post as a flagged post
    #Will be triggered from the frontend when the support agent presses the button for a post to be offensive.
    #From frontend, two actions will be triggered. One would set is_offensive as True in the ticket database, and the other would use the post request here to add it to the flagged post class
    def post(user,self):
        if user.role_id ==2:
            args = request.get_json(force = True)
            flagger_id = None
            creator_id = None
            ticket_id = None
            flagger = None
            creator = None
            ticket = None
            try:
                flagger_id = args["flagger_id"]
            except:
                abort(403, message = "Please pass the flagger ID.") 
            try:   
                creator_id = args["creator_id"]
            except:
                abort(403, message = "Please pass the creator ID.")
            try:
                ticket_id = args["ticket_id"]
            except:
                abort(403, message = "Please pass the Ticket ID.")
            try:
                flagger = User.query.filter_by(user_id = flagger_id, role_id = 2).first()
                if flagger is None:
                    raise invalidFlaggerException
            except invalidFlaggerException:
                abort(403, message = "The person who flagged must be a support agent.")
            
            try:
                creator = User.query.filter_by(user_id = creator_id, role_id = 1).first()
                if creator is None:
                    raise invalidCreatorException
            except invalidCreatorException:
                abort(403, message = "The person who created the post must be a student.")
            
            try:
                ticket = Ticket.query.filter_by(ticket_id = ticket_id, creator_id = creator_id).first()
                if ticket is None:
                    raise invalidTicketException
            except:
                abort(403, message ="The referenced ticket is not created by the referenced person/ the ticket doesn't exist in the first place.")
            flagged_post = Flagged_Post(creator_id = creator_id, ticket_id = ticket_id, flagger_id = flagger_id, is_rejected = False, is_approved = False)
            db.session.add(flagged_post)
            db.session.commit()
            return jsonify({"status": "success"})
        else:
            abort(404, message = "You are not authorized to access this feature.")
    
    @token_required
    def patch(user, self):
        if user.role_id == 3:
            args = request.get_json(force = True)
            ticket_id = args["ticket_id"]
            is_approved = None
            is_rejected = None
            try:
                if args["is_approved"] is not None:
                    is_approved = args["is_approved"]
            except:
                if args["is_rejected"] is not None:
                    is_rejected = args["is_rejected"]
            flagged_post = Flagged_Post.query.filter_by(ticket_id = ticket_id).first()
            if is_approved is not None:
                flagged_post.is_approved = is_approved
                flagged_post.is_rejected = False
            elif is_rejected is not None:
                flagged_post.is_approved = False
                flagged_post.is_rejected = is_rejected
            db.session.commit()
            return jsonify({"status": "success"})
            
        else:
            abort(404, message = "You are not authorized to access this feature.")
            
class Login(Resource):
    def post(self):
        if request.is_json:
            email = request.json["email"]
            password = request.json["password"]
        else:
            email = request.form["email"]
            password = request.form["password"]
        test = User.query.filter_by(email_id=email).first()
        # print(test)
        if (test is None):
            abort(409,message="User does not exist")
        elif (test.password == password):
            token = jwt.encode({
                'user_id': test.user_id,
                'exp': datetime.utcnow() + timedelta(minutes=80)
            }, Config.SECRET_KEY, algorithm="HS256")
            # access_token = create_access_token(identity=email)
            # print(token)
            return jsonify({"message":"Login Succeeded!", "token":token,"user_id":test.user_id,"role":test.role_id})
        else:
            abort(401, message="Bad Email or Password")
            
from application.utils import add_users_import    
class ImportResourceUser(Resource):
    @token_required
    def post(user,self):
        #print(request.files)
        file=request.files['file']
        file.save(file.filename)
        if(user.role_id==3):
            add_users_import.s(csv_file_path=file.filename, eid=user.email_id).apply_async()
            return jsonify({"message":"File uploaded successfully"})
        else:
            abort(401,message="You are not authorized to access this feature")

class CategoryAPI(Resource):
    @token_required
    def get(user, self):
        categories = [cat.category for cat in db.session.query(Category).all()]
        return jsonify({'data': categories})
    
    @token_required
    def post(user ,self):
        if user.role_id==3:
            try:
                category = request.json['category']
            except:
                abort(400, message='category is required and should be string')
            new_cat = Category(category=category)
            headers = {
                    "Api-Key": LocalDevelopmentConfig.DISCOURSE_API_KEY,
                    "Api-Username": LocalDevelopmentConfig.DISCOURSE_API_USERNAME
                    }
            data ={
                "name": category
            }
            
            url = "http://localhost:4200/categories"
            request= requests.post(url, json=data, headers=headers)
            
            if request.status_code == 200:
                db.session.add(new_cat)
                db.session.commit()
                return jsonify({"status": "success"})
            else:
                db.session.rollback()
                return jsonify({"status": "failed"})
                # db.session.rollback()
        else: 
            abort(403,message="Unauthorized")


class DiscourseUser(Resource):
    
    @token_required
    def post(user,self):
        
        data = request.get_json()
        data = json.loads(data['data'])
    
        email = data['email_id']
        password = data['password']
        username = data['username']
        role_id = data['role_id']
        print(email,password,username, role_id)
        data = None
        headers = None
        # print(user.role_id)
        # print("debug 1")
        
        if role_id == 3 or role_id == 4:
            #user1 = User.query.filter_by(email_id = email).first()
            #print(user1.user_name)
            # print("debug 2")
            user1 = User.query.filter_by(email_id = email).first()
            data1 = {
                    "name": user1.user_name,
                    "email": email,
                    "password": password,
                    "username": username,
                    "active": "true",
                    "approved": "true"
                    
                }
            
            
        elif role_id == 1 or role_id == 2:
            try:
                # print("debug 3")
                user1 = User.query.filter_by(email_id = email).first()
                # print(user1)
                data1 = {
                    "name": user1.user_name,
                    "email": email,
                    "password": password,
                    "username": username,
                    "active": "true",
                    "approved": "false"
                    
                }
            except:
                # print("excep2 1")
                abort(404, message = "User does not exist.")

        # print("debug 4")
        headers = {
                    "Api-Key": LocalDevelopmentConfig.DISCOURSE_API_KEY,
                    "Api-Username": LocalDevelopmentConfig.DISCOURSE_API_USERNAME
                    }
        # print("debug 5")
        url = "http://localhost:4200/users"
        # print("debug 6")
        requ = requests.post(url,json=data1, headers = headers)
        resp = requ.json()
        # print("debug 7")
        print(resp)
        # print("Response status code:", requ.status_code)
        # print("Response content:", requ.content)
        if requ.status_code == 200:
            if resp['success']:
                print(resp)
                # user disoucrse id in user 
                # print(resp)
                user1.discourse_userid = resp["user_id"]
                user1.discourse_username = username 
                user1.discourse_password = password
                db.session.add(user1)
                db.session.commit()
                
                return jsonify({
                    "status": "success",
                    "active": resp["active"],
                    "message": resp["message"]
                    }) 
                
            else:    
                return jsonify({"status": "failed", "message":resp["message"] })
                
        else:
            return jsonify({"status": "failed", "message": "User in Discourse could not be created."}),requ.status_code
        #return "pass"

        #return jsonify({"status": "failed", "message": "User in Discourse could not be created."})
    
    

class DiscoursePostCreation(Resource):
    
    @token_required
    def post(user,self):

        try:
           
            user = User.query.filter_by(user_id = user.user_id).first()
           
        except:
            
            abort(404, message = "User does not exist.")
        try:
            
            url = "http://localhost:4200/posts"
          
            headers = {
                    "Api-Key": LocalDevelopmentConfig.DISCOURSE_API_KEY,
                    "Api-Username": user.discourse_username
                    }
            
            args = request.get_json(force = True)
           
            ticket_id = None
            title = None
            raw = None
            # category = 0
            # target_recipients = "system"
            # archetype = "private_message"

            if args["title"]:
               
                title = args["title"]
            else: 
                
                abort(400, message = "Please provide a title.")
            
            if args["message_body"]:
                
                raw = args["message_body"]
            else:
             
                abort(400, message = "Please provide the raw content.")
            
            
            
            if args["ticket_id"]:
               
                ticket_id = args["ticket_id"]

            else:
              
                abort(400, message = "Please provide the ticket ID.")
                
            data = {
                "title": title,
                "raw": raw,              
                "category": 0,
                "target_recipients": "discourse_support",
                "archetype": "private_message"
            }
          

            print(json.dumps(data))      
            request1 = requests.post(url, json = data, headers = headers)
            print(request1.content)
            print("debug 17")
            if request1.status_code == 200:
                resp = request1.json() 
                print("debug 20")
                print(resp)
                post_id = None
                topic_id = None
                topic_slug = None
                display_username = None
                created_at = None
                updated_at = None
                cooked = None
                reply_count = None
                reply_to_post_number = None
                quote_count = None
                incoming_link_count = None
                reads = None
                readers_count = None
                score = None
                yours = None
                display_username = None
                primary_group_name = None
                flair_name = None
                flair_url = None
                flair_bg_color = None
                flair_color = None
                flair_group_id = None
                version = None
                can_edit = None
                can_delete = None
                can_recover = None
                can_see_hidden_post = None
                can_wiki = None
                user_title = None
                bookmarked = None
                actions_summary = None
                moderator = None
                admin = None
                staff = None
                user_id = None
                draft_sequence = None
                hidden = None
                trust_level = None
                deleted_at = None
                user_deleted = None
                edit_reason = None
                can_view_edit_history = None
                wiki = None
                reviewable_id = None
                reviewable_score_count = None
                reviewable_score_pending_count = None
                mentioned_users = None
             
                if resp["id"]:
                    post_id = resp["id"]
                
                if resp["topic_id"]:
                    topic_id = resp["topic_id"]
                
                if resp["topic_slug"]:
                    topic_slug = resp["topic_slug"]
                # print("debug 343")
                if resp["created_at"]:
                    created_at = resp["created_at"]
                # print("debug 343")
                if resp["updated_at"]:
                    updated_at = resp["updated_at"]
                # print("debug tes")
                if resp["cooked"]:
                    cooked = resp["cooked"]
                # print("debug df")
                if resp["reply_count"]:
                    reply_count = resp["reply_count"]
                # print("debug df")
                if resp["reply_to_post_number"]:
                    reply_to_post_number = resp["reply_to_post_number"]
                # print("debug df")
                if resp["quote_count"]:
                    quote_count = resp["quote_count"]
                # print("debug df")
                if resp["incoming_link_count"]:
                    incoming_link_count = resp["incoming_link_count"]
                # print("debug df")
                if resp["reads"]:
                    reads = resp["reads"]
                print("debug df")
                if resp["readers_count"]:
                    readers_count = resp["readers_count"]
                print("debug df")
                if resp["score"]:
                    score = resp["score"]
                print("debug df")
                if resp["yours"]:
                    yours = resp["yours"]
                print("debug df")
                if resp["display_username"]:
                    display_username = resp["display_username"]
                print("debug df")
                if resp["primary_group_name"]:
                    primary_group_name = resp["primary_group_name"]
                print("debug df")
                if resp["flair_name"]:
                    flair_name = resp["flair_name"]
                print("debug df")
                if resp["flair_url"]:
                    flair_url = resp["flair_url"]
                print("debug df")
                if resp["flair_bg_color"]:
                    flair_bg_color = resp["flair_bg_color"]
                print("debug df")
                if resp["flair_color"]:
                    flair_color = resp["flair_color"]
                print("debug df")
                if resp["flair_group_id"]:
                    flair_group_id = resp["flair_group_id"]
                print("debug df")
                if resp["version"]:
                    version = resp["version"]
                print("debug df")
                if resp["can_edit"]:
                    can_edit = resp["can_edit"]
                print("debug df")
                if resp["can_delete"]:
                    can_delete = resp["can_delete"]
                print("debug df")
                if resp["can_recover"]:
                    can_recover = resp["can_recover"]
                print("debug df")
                if resp["can_see_hidden_post"]:
                    can_see_hidden_post = resp["can_see_hidden_post"]
                print("debug df")
                if resp["can_wiki"]:
                    can_wiki = resp["can_wiki"]
                print("debug df")
                if resp["user_title"]:
                    user_title = resp["user_title"]
                print("debug df")
                if resp["bookmarked"]:
                    bookmarked = resp["bookmarked"]
                print("debug df")
                if resp["actions_summary"]:
                    actions_summary = resp["actions_summary"]
                print("debug df")
                if resp["moderator"]:
                    moderator = resp["moderator"]
                print("debug df")
                if resp["admin"]:
                    admin = resp["admin"]
                print("debug df")
                if resp["staff"]:
                    staff = resp["staff"]
                print("debug df")
                if resp["user_id"]:
                    user_id = resp["user_id"]
                print("debug df")
                if resp["draft_sequence"]:
                    draft_sequence = resp["draft_sequence"]
                print("debug df")
                if resp["hidden"]:
                    hidden = resp["hidden"]
                print("debug df9")
                if resp["trust_level"]:
                    trust_level = resp["trust_level"]
                print("debug df8")
                if resp["deleted_at"]:
                    deleted_at = resp["deleted_at"]
                print("debug df7")
                if resp["user_deleted"]:
                    user_deleted = resp["user_deleted"]
                print("debug df6")
                if resp["edit_reason"]:
                    edit_reason = resp["edit_reason"]
                print("debug df5")
                if resp["can_view_edit_history"]:
                    can_view_edit_history = resp["can_view_edit_history"]
                print("debug df4")
                if resp["wiki"]:
                    wiki = resp["wiki"]
                print("dfsdfds")
                
                print("debug 22") 
                new_discourse_post = DiscoursePost(post_id = post_id, 
                                                   topic_id = topic_id,  
                                                   created_at = created_at, 
                                                   updated_at = updated_at, 
                                                #    cooked = cooked, 
                                                   reply_count = reply_count, 
                                                   reply_to_post_number = reply_to_post_number, 
                                                #    quote_count = quote_count, 
                                                #    incoming_link_count = incoming_link_count, 
                                                #    reads = reads, 
                                                #    readers_count = readers_count, 
                                                #    score = score, 
                                                #    yours = yours, 
                                                   display_username = display_username, 
                                                   primary_group_name = primary_group_name, 
                                                #    flair_name = flair_name, 
                                                #    flair_url = flair_url, 
                                                #    flair_bg_color = flair_bg_color, 
                                                #    flair_color = flair_color, 
                                                #    flair_group_id = flair_group_id, 
                                                   version = version, 
                                                   can_edit = can_edit, 
                                                   can_delete = can_delete, 
                                                   can_recover = can_recover,
                                                   can_see_hidden_post = can_see_hidden_post, 
                                                   can_wiki = can_wiki, 
                                                   user_title = user_title, 
                                                #    bookmarked = bookmarked, 
                                                #    actions_summary = actions_summary, 
                                                   moderator = moderator, 
                                                   admin = admin, 
                                                   staff = staff, 
                                                   user_id = user_id, 
                                                #    draft_sequence = draft_sequence, 
                                                   hidden = hidden, 
                                                   trust_level = trust_level, 
                                                   deleted_at = deleted_at, 
                                                   user_deleted = user_deleted, 
                                                   edit_reason = edit_reason, 
                                                   can_view_edit_history = can_view_edit_history, 
                                                   wiki = wiki)
                db.session.add(new_discourse_post)
                print("debug 202")
                print(ticket_id)
                ticket = Ticket.query.filter_by(ticket_id = ticket_id).first()
                print("debug 2022")
                ticket.discourse_post_id = post_id
                print("debug 202222")
                db.session.commit()
                print("debug 24")
                return jsonify({
                    "status": "success",
                    "message": "Post in Discourse created successfully."
                    }) 
            else:
                print("debug 18")
                # abort(422, message = "Post in Discourse could not be created.")
                return jsonify({"status": "failed", "message": "Post in Discourse could not be created."}), request.status_code
        except:
            print("debug 19")
            abort(404, message = "Discourse server not reachable.")
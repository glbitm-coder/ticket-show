from datetime import datetime
import os
from flask import jsonify, make_response, request
from flask_cors import cross_origin
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from application import db
from application.Models.show import Show

from application.Models.theatre import Theatre

from ..validation import BadRequest, BusinessValidationError, NotFoundError, UnAuthorizedError
from ..Models.user import User
from ..Models.role import Role
from werkzeug.security import check_password_hash
from flask_restful import Resource, fields, marshal_with
from ..Parser.showParser import show_parser



class ShowAPI(Resource):

    @jwt_required()
    def post(self, user_id = None, theatre_id = None):

        errorMessages = []
        current_user_id = get_jwt_identity()
        if user_id is not None and user_id != current_user_id:
            errorMessages.append("You are not authorized to see the page")
            return UnAuthorizedError(error_messages=errorMessages)
        
        user = User.query.filter_by(id = user_id).first()
        if not user:
            errorMessages.append("User not found")
            return NotFoundError(error_messages=errorMessages)
        
        theatre = Theatre.query.filter_by(id = theatre_id).first()
        if not theatre:
            errorMessages.append("Theatre not found")
            return NotFoundError(error_messages=errorMessages)
        
        args = show_parser.parse_args()
        input_name = args.get("input_name", None)
        input_price = args.get("input_price", None)
        input_date = args.get("input_date", None)
        input_startTime = args.get('input_startTime', None)
        input_endTime = args.get('input_endTime', None)
        input_tags = args.get('input_tags', None)

        if not input_name:
            errorMessages.append("Name cannot be empty")
        if not input_price:
            errorMessages.append("Price cannot be empty")
        if not input_date:
            errorMessages.append("Date cannot be empty")
        if not input_startTime:
            errorMessages.append("Start time cannot be empty")
        if not input_endTime:
            errorMessages.append("End time cannot be empty")
        if not input_tags:
            errorMessages.append("Tags cannot be empty")
        
        if len(errorMessages) != 0:
            raise BusinessValidationError(error_messages=errorMessages)
        
        parsed_date = datetime.strptime(input_date, "%Y-%m-%d")
        parsed_start_time = datetime.strptime(input_startTime, "%H:%M")
        parsed_end_time = datetime.strptime(input_endTime, "%H:%M")

        existing_show = Show.query.filter_by(
                storedName=input_name,
                storedPrice=input_price,
                date=parsed_date,
                startTime=parsed_start_time.time(),
                endTime=parsed_end_time.time(),
                storedTags=input_tags
            ).first()

        if existing_show:
            theatre.shows.append(existing_show)
            db.session.commit()
            return make_response(jsonify({
                    "message" : "Show already created and now the show is assigned to this theatre also"
                }), 201)
        else:
            # If the show does not exist, create a new show and associate it with the theatre
            new_show = Show(
                storedName=input_name,
                storedPrice=input_price,
                date=parsed_date,
                startTime=parsed_start_time.time(),
                endTime=parsed_end_time.time(),
                storedTags=input_tags,
                createdby_id=user.id
            )
            theatre.shows.append(new_show)
            db.session.add(new_show)
            db.session.commit()
            return make_response(jsonify({
                    "message" : "Show created successfully"
                }), 201)


        

        
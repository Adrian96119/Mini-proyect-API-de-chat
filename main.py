from flask import Flask,request,Response, jsonify
from flask_pymongo import PyMongo, ObjectId
import hashlib
from bson.json_util import loads, dumps
import json
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

sia = SentimentIntensityAnalyzer() #dejo ya inicialidada la instancia de la libreria nlkt

app = Flask(__name__) #creo el objeto aplicacion

app.config["MONGO_URI"]= "mongodb://localhost:27017/api"     #donde esta la base de datos

mongo = PyMongo(app) #conecto mi base de datos con mi app

#bienvenida
@app.route('/') #doy la bienvenida solo con la url original
def hola_mundo():
  return '<h1>Hola Mundo!!!!!!!!!!!!<h1>'
   

#USUARIOS------------------------------------------

@app.route('/create_user',methods = ["POST"]) #con esto creo usuarios
def create_user():
    username = request.json['username'] #CON UN USERNAME
    password = request.json['password'] #UNA CONTRASEÑA QUE VOY A CODIFICARLA DESPUES
    email = request.json['email'] #UN EMAIL

    
    h = hashlib.md5()   #CON LA LIBRERIA HASLIB CODIFICO LA CONTRASEÑA DEL USER PARA QUE NO SE VEA EN LA BASE DE DATOS
    h.update(password.encode('utf-8'))
    hash = h.hexdigest()

    id = mongo.db.users.insert(  #INSERTO LAS VARIABLES QUE CONTENDRAN LO QUE INGRESE DESDE LA API EN UNA NUEVA COLECCION DE USERS
            {
                "username": username,
                "password": hash,
                "email": email

            }
        )

    res = {
            'id': str(id), #EL RETORNO DE MI FUNCION CON UN ID UNICO POR USUARIO
            'username':username,
            'password':hash,
            'email': email
        }

    return res
    

@app.route('/alls_users',methods = ["GET"]) #saco todos los usuarios con sus datos
def all_users():
    users = mongo.db.users.find()
    respuesta = dumps(users) #METO DUMPS PARA QUE PUEDA LUEGO CONVERTIRME LA RESPUESTA EN JSON
    resjson = Response(respuesta, mimetype='application/json') #para que me responda con un JSON
    return resjson
   
    
  
@app.route('/user_id/<username>',methods=["GET"]) #me saca con el nombre el id del user
def id_user(username):
    h = mongo.db.users.find_one({'username':username})
    r = dumps(h["_id"])
    rjson = Response(r, mimetype="application/json")  #mimetype para que en postman me aparezca como json 
    return rjson

@app.route('/user_data/<id>',methods=["GET"]) #con el id del user, saco todos sus datos
def datos_users(id):
    p = mongo.db.users.find_one({'_id':ObjectId(id)})
    salida = {"username": p["username"],"password":p["password"],"email":p["email"]}
    return salida
    
#GRUPOS O CHATS -----------------------------------------------
   
@app.route('/create_group',methods=["POST"]) #creo un grupo de chat con los miembros
def create_group():
    groupName = request.json["name"] #CREO UN NOMBRE
    asunto = request.json["asunto"] #CREO UN ASUNTO
    members = request.json["members"] #CREO A LOS MIEMBROS
    
    
  
    

     
    id = mongo.db.chats.insert(
            { 
            "name":groupName,
            "asunto": asunto,
            "members": members
            
            
            }
            
        )
    
    res = {'id': str(id),
            'name': groupName,
            'asunto': asunto,
            'members': members
            
            
        }
        
    return res
    
@app.route('/group_id/<name>',methods=["GET"]) #me saca el id del chat
def id_chat(name):
    h = mongo.db.chats.find_one({'name':name})
    r = dumps(h["_id"])
    rjson = Response(r, mimetype="application/json")  #mimetype para que en postman me aparezca como json 
    return rjson

@app.route('/all_groups',methods = ["GET"]) #saco todos los chats con sus datos
def all_chats():
    chats = mongo.db.chats.find()
    respuesta = dumps(chats)
    resjson = Response(respuesta, mimetype='application/json')
    return resjson

@app.route('/group_data/<id>',methods=["GET"]) #con el id del chat, saco todos sus datos
def datos_chats(id):
    h = mongo.db.chats.find_one({'_id':ObjectId(id)}) 
    salida = {'name':h["name"],'asunto':h["asunto"], 'members':h["members"]}
    return jsonify(salida)

#MENSAJES -----------------------------------------------------------   
@app.route('/create_messages',methods = ["POST"])
def create_message():
    
    
    user = request.json["user"] #meto el id de user
    chat = request.json["chat"] #meto el id del chat
    mensaje = request.json["message"] #introduzco el mensaje del cual me sacara por cada uno un id

    cc = mongo.db.chats.find_one({"_id":ObjectId(chat)})
    miembros = cc["members"]

    if user in miembros.values(): #creo una condicion, si el id no esta en el chat, no puedes enviar mensajes por no estar en el grupo
        message = mongo.db.mensajes.insert(
                    {
                        "user": user,
                        "chat": chat,
                        "message": mensaje
                    }
                    )
        res = {
                    "id": str(message),
                    "user": user,
                    "chat": chat,
                    "message": mensaje
                }
        return res
    else:
        return 'no te quieren'


@app.route('/conversacion/<chat_id>',methods=["GET"]) #introduzco el id del chat y me saca la conversacion entera
def chat(chat_id):
    cm = mongo.db.mensajes.find()
    l = list(cm)
    chat = [i for i in l if chat_id in i.values()]
    resp = dumps(chat)
    resjson = Response(resp, mimetype='application/json')
    return resjson 

   
@app.route('/mensajes_user/<id_user>/<id_chat>',methods = ["GET"]) #dando el id_user y el id_chat saco
#todos los mensajes del usuario de ese chat
def mensajes_user(id_user,id_chat):
    cm = mongo.db.mensajes.find()
    l = list(cm)
    chat = [i for i in l if id_chat in i.values()]
    mensajeUser = [i for i in chat if id_user in i.values()]
    if id_user and id_chat in mensajeUser[0].values(): #le pongo una condicion por si no pongo bien alguno de los parametros me genere mi error 500 

        resp = dumps(mensajeUser)
        resjson = Response(resp, mimetype='application/json')
        return resjson
    
#SENTIMIENTOS -----------------------------------       
@app.route('/chat/sentimiento/<id_chat>',methods = ["GET"]) #me saca el sentimiento de las conver con el id del chat
def sentimiento_chat(id_chat):
    
    cm = mongo.db.mensajes.find()
    l = list(cm)
    chat = [i for i in l if id_chat in i.values()] #QUE ME DE SOLO LOS MENSAJES DONDE ESTE EL ID DEL CHAT QUE PIDA
    conver = [i["message"] for i in chat] #RECORRO TODA LA LISTA Y ME QUEDO SOLO CON LOS MENSAJES
    conversacion = "".join(conver) #CONVIERTO EL MENSAJE A STRING PARA ANALIZAR EL SENTIMIENTO
    
    analisis_conver = sia.polarity_scores(conversacion)
    return analisis_conver #DEVUELVO EL SENTIMIENTO DE TODA LA CONVERSACION EN GENERAL DE ESE CHAT QUE PIDE EL CLIENTE


@app.route('/user/sentimiento/<id_chat>/<id_user>',methods = ["GET"]) #me saca el sentimiento de los user por su id y su chat
def sentimiento_user(id_chat,id_user):
    cm = mongo.db.mensajes.find()
    l = list(cm)
    chat = [i for i in l if id_chat in i.values()] #PRIMERO QUE ME SAQUE LOS MENSAJES DEL CHAT QUE PIDA EL CLIENTE
    mensajeUser = [i for i in chat if id_user in i.values()] #Y ADEMAS DEL USER QUE ME DIGA
    only_mensajes = [i["message"]for i in mensajeUser] #ME SACA TODOS SUS MENSAJES
    sentUser = "".join(only_mensajes) #CONVIERTO A STRINGS TODOS SUS MENSAJES
    analisis_user = sia.polarity_scores(sentUser) #ANALIZO TODOS LOS MENSAJES DE ESE CHAT DONDE PARTICIPÓ 
    return analisis_user #RETORNA EL SENTIMIENTO GENERAL DEL USUARIO EN EL CHAT QUE NOS HAN PEDIDO




@app.errorhandler(500)
def algo_mal(error=None):
    mensaje_error = jsonify({
    'message': 'debes añadir todos los campos o parametros, y que estén bien escritos',
    'error': 500
    })
    mensaje_error.status_code = 500
    return mensaje_error


######FUNCIONES DE PROGRAMACION DEFENSIVA

#PARA CADA ERROR QUE ME HA SALIDO AL HACER PETICIONES O PUBLICACIONES EN POSTMAN HE IDO CUBRIENDO LOS ERRORES
#CON MENSAJES MIOS PARA SABER LO QUE SON Y QUE ME SEA MAS FACIL CONTROLARLOS.
@app.errorhandler(404)
def not_found(error=None):
    mensaje_error = jsonify({
        'message':'pagina no encontrada, introduzca bien la URI, o los datos que enviar',
        'error': 404
    })
    mensaje_error.status_code = 404
    return mensaje_error


@app.errorhandler(405)
def metodo_erroneo(error=None):
    mensaje_error = jsonify({
        'message':'el metodo utilizado no es el adecuado, tienes: (post,get,put...)',
        'error': 405
    })
    mensaje_error.status_code = 405
    return mensaje_error
    
  

@app.errorhandler(400)
def clave_inexistente(error=None):
    mensaje_error = jsonify({
        'message':'acceso a una clave que no existe',
        'error': 400
    })
    mensaje_error.status_code = 400
    return mensaje_error
      
    
   






    


  
        






    

    

    







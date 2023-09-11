import os
from flask import Flask, session, flash, g, request, json
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, UserHousehold, Household, SellerExpertise, OwnershipOccupancy, Associations, Roof, Basement, RoleType, FrequencyType, AssociationType
from sqlalchemy.exc import IntegrityError

CURR_USER_KEY = "curr_user"

app = Flask(__name__)
app.app_context().push()

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://react-capstone-2-dbserver.postgres.database.azure.com:5432/?user=dbadmin&password=Dbpassword#&sslmode=require&dbname=postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') # DEV
# app.config['SECRET_KEY'] = 'supersecret' # LOCAL
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['CORS_HEADERS'] = 'Content-Type'
debug = DebugToolbarExtension(app)

connect_db(app)
# db.create_all()

############################## AUTH ROUTES ##############################

def do_login(user):
    """Log a user in."""
    session[CURR_USER_KEY] = user.id

def do_logout():
    """Log a user out."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

@app.before_request
def add_user_to_g():
    """If we are logged in, add curr_user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
        print('g.user added to session: ' + str(g.user))

    else:
        g.user = None

@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = '*'
    return response       

@app.route("/api/register", methods=["GET", "POST", "OPTIONS"])
def register():
    print(request.json)

    username = request.json.get("username")
    password = request.json.get("password")

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

    try:
        existingUser = User.query.filter(username == User.username).all()
        if existingUser:
            return ("Error: Username Already Taken")

        user = User.register(username, password)
        db.session.add(user)
        db.session.commit()

    except IntegrityError as e:
        flash("Username already taken", 'danger')

    do_login(user)
    session["user_id"] = user.id

    flash("You are now registered!", "success")
    return str(user.id)

@app.route("/api/login", methods=["GET", "POST", "OPTIONS"])
def login():
    print('Login start')
    print(request.json)

    username = request.json.get("username")
    password = request.json.get("password")

    user = User.authenticate(username, password)

    if user:
        do_login(user)
        print(user)
        flash(f"Welcome, {user.username}!", "success")

        # Keep User Logged In
        session["user_id"] = user.id
        print(user.id)
        return str(user.id)

    else:        
        return ("Error: Login not found")


@app.route('/api/logout')
def logout():
    """Handle user logout."""

    do_logout()
    flash('You have been logged out.', 'success')


############################## USER ROUTES ##############################

@app.route("/api/user", methods=["GET", "OPTIONS"])
def getCurrentUser():
    print("ARGS: " + request.args.get("userId"))

    userId = request.args.get("userId")
    print(userId)
        
    # Get user by id
    currentUser = User.query.filter(User.id == userId).one()

    # Return user as json
    return currentUser.as_dict()

# TODO Update

############################## HOUSEHOLD ROUTES ##############################

def row2dict(r):
    return {c.name: str(getattr(r, c.name)) for c in r.__table__.columns}


@app.route("/api/households", methods=["GET", "OPTIONS"])
def getUserHouseholds():
    print("ARGS: " + str(request.args))

    userId = request.args.get("userId")
        
    # Get list of households for user
    households = UserHousehold.query\
        .filter(UserHousehold.userID == userId)\
        .all()

    if not households:
        return []

    # Create returnable json list of households, turn each row into dict object
    householdsList = json.dumps(households, default = lambda x:x.as_dict())

    # Return households as json
    return householdsList

@app.route("/api/household", methods=["GET", "OPTIONS"])
def getHousehold():
    print("ARGS: " + str(request.args))

    householdId = request.args.get("householdId")
        
    # Get household by id
    household = Household.query.filter(Household.id == householdId).one()

    # Return household as json
    return household.as_dict()

@app.route("/api/household", methods=["POST", "OPTIONS"])
def createHousehold():
    print("ARGS: " + str(request.json))
        
    # Create new household class
    newHousehold = Household()
    userId = request.json.get("userId")
    newHousehold.name = request.json.get("name")
    newHousehold.street_address = request.json.get("address")
    newHousehold.city = request.json.get("city")
    newHousehold.state = request.json.get("state")
    newHousehold.zip = request.json.get("zip")
    newHousehold.notes = request.json.get("notes")  

    # Add household to DB
    db.session.add(newHousehold)
    db.session.commit()

    # Create new record for user household class
    newUserHousehold = UserHousehold()
    newUserHousehold.userID = userId
    newUserHousehold.householdID = newHousehold.id

    # Add user household to DB
    db.session.add(newUserHousehold)
    db.session.commit()

    # Return household as json
    return newHousehold.as_dict()

@app.route("/api/household", methods=["PATCH", "OPTIONS"])
def updateHousehold():
    print(request.json)
    householdId = request.json.get("id")
         
    # Get household by id
    household = Household.query.filter(Household.id == householdId).one()
    
    # Update household class
    household.name = request.json.get("name")
    household.street_address = request.json.get("address")
    household.city = request.json.get("city")
    household.state = request.json.get("state")
    household.zip = request.json.get("zip")
    household.notes = request.json.get("notes")  

    # Update household in DB
    db.session.commit()

    # Return household as json
    return household.as_dict()

@app.route("/api/household/delete", methods=["POST", "OPTIONS"])
def deleteHousehold():

    print(request.json)
    householdId = request.json.get("householdId")
         
    # Get household by id
    household = Household.query.filter(Household.id == householdId).one()
    
    db.session.delete(household)
    db.session.commit()

    # Return if complete
    return "Deleted"

############################## SELLER EXPERTISE ROUTES ##############################

@app.route("/api/sellerExpertise", methods=["GET", "OPTIONS"])
def getSellerExpertise():
    print("ARGS: " + str(request.args))

    householdId = request.args.get("householdId")
        
    # Get sellerExpertise by id
    # query by house id, if result set has a row, return row. else, return empty {}

    expertiseRowCount = SellerExpertise.query.filter(SellerExpertise.id == householdId).count()

    if expertiseRowCount > 0:
        sellerExpertise = SellerExpertise.query.filter(SellerExpertise.id == householdId).one()
        return sellerExpertise.as_dict()

    # Return sellerExpertise as json
    return ""

@app.route("/api/sellerExpertise", methods=["PATCH", "OPTIONS"])
def updateSellerExpertise():
    print(request.json)
    householdId = request.json.get("id")
         
    # Get sellerExpertise by householdId
    sellerExpertise = SellerExpertise.query.filter(SellerExpertise.id == householdId).one()
    
    # Update sellerExpertise class
    sellerExpertise.hasExpertise = request.json.get("hasExpertise")
    sellerExpertise.isLandlord = request.json.get("isLandlord")
    sellerExpertise.isRealEstateLicensee = request.json.get("isRealEstateLicensee")
    sellerExpertise.notes = request.json.get("notes")  

    # Update sellerExpertise in DB
    db.session.commit()

    # Return sellerExpertise as json
    return sellerExpertise.as_dict()

@app.route("/api/sellerExpertise", methods=["POST", "OPTIONS"])
def createSellerExpertise():
    print(request.json)
        
    # Create new seller expertise class
    newSellerExpertise = SellerExpertise()
    newSellerExpertise.householdID = request.json.get("householdId")
    newSellerExpertise.hasExpertise = request.json.get("hasExpertise")
    newSellerExpertise.isLandlord = request.json.get("isLandlord")
    newSellerExpertise.isRealEstateLicensee = request.json.get("isRealEstateLicensee")
    newSellerExpertise.notes = request.json.get("notes")  

    # Add seller expertise to DB
    db.session.add(newSellerExpertise)
    db.session.commit()

    # Return sellerExpertise as json
    return newSellerExpertise.as_dict()

############################## OWNERSHIP / OCCUPANCY ROUTES ##############################

@app.route("/api/ownershipOccupancy", methods=["GET", "OPTIONS"])
def getOwnershipOccupancy():
    print("ARGS: " + str(request.args))

    householdId = request.args.get("householdId")
        
    # Get ownershipOccupancy by id
    # query by house id, if result set has a row, return row. else, return empty {}

    ownershipRowCount = OwnershipOccupancy.query.filter(OwnershipOccupancy.id == householdId).count()

    if ownershipRowCount > 0:
        ownershipOccupancy = OwnershipOccupancy.query.filter(OwnershipOccupancy.id == householdId).one()
        return ownershipOccupancy.as_dict()

    # Return ownershipOccupancy as json
    return ""

@app.route("/api/ownershipOccupancy", methods=["PATCH", "OPTIONS"])
def updateOwnershipOccupancy():
    print(request.json)
    householdId = request.json.get("id")
         
    # Get ownershipOccupancy by id
    ownershipOccupancy = OwnershipOccupancy.query.filter(OwnershipOccupancy.id == householdId).one()
    
    # Update ownershipOccupancy class
    ownershipOccupancy.householdID = request.json.get("householdId")
    ownershipOccupancy.roleTypeID = request.json.get("roleTypeId")
    ownershipOccupancy.mostRecentOccupation = request.json.get("mostRecentOccupation")
    ownershipOccupancy.isOccupiedBySeller = request.json.get("isOccupiedBySeller")
    ownershipOccupancy.sellerOccupancyHistory = request.json.get("sellerOccupancyHistory")
    ownershipOccupancy.hasHadPets = request.json.get("hasHadPets")
    ownershipOccupancy.purchaseDate = request.json.get("PurchaseDate")
    ownershipOccupancy.notes = request.json.get("notes")  

    # Update ownershipOccupancy in DB
    db.session.commit()

    # Return ownershipOccupancy as json
    return ownershipOccupancy.as_dict()

@app.route("/api/ownershipOccupancy", methods=["POST", "OPTIONS"])
def createOwnershipOccupancy():
    print(request.json)
        
    # Create new ownershipOccupancy class
    newOwnershipOccupancy = OwnershipOccupancy()
    newOwnershipOccupancy.householdID = request.json.get("householdId")
    newOwnershipOccupancy.roleTypeID = request.json.get("roleTypeId")
    newOwnershipOccupancy.mostRecentOccupation = request.json.get("mostRecentOccupation")
    newOwnershipOccupancy.isOccupiedBySeller = request.json.get("isOccupiedBySeller")
    newOwnershipOccupancy.sellerOccupancyHistory = request.json.get("sellerOccupancyHistory")
    newOwnershipOccupancy.hasHadPets = request.json.get("hasHadPets")
    newOwnershipOccupancy.purchaseDate = request.json.get("PurchaseDate")
    newOwnershipOccupancy.notes = request.json.get("notes")

    # Add ownershipOccupancy to DB
    db.session.add(newOwnershipOccupancy)
    db.session.commit()

    # Return ownershipOccupancy as json
    return newOwnershipOccupancy.as_dict()

############################## ASSOCIATIONS ROUTES ##############################

@app.route("/api/associations", methods=["GET", "OPTIONS"])
def getAssociations():
    print("ARGS: " +str(request.args))

    householdId = request.args.get("householdId")
        
    # Get associations by id
    # query by house id, if result set has a row, return row. else, return empty {}

    associationsRowCount = Associations.query.filter(Associations.id == householdId).count()

    if associationsRowCount > 0:
        associations = Associations.query.filter(Associations.id == householdId).one()
        return associations.as_dict()

    # Return associations as json
    return ""

@app.route("/api/associations", methods=["PATCH", "OPTIONS"])
def updateAssociations():
    print(request.json)
    householdId = request.json.get("id")
         
    # Get associations by id
    associations = Associations.query.filter(Associations.id == householdId).one()
    
    # Update associations class
    associations.householdID = request.json.get("householdId")
    associations.associationTypeID = request.json.get("associationTypeID")
    associations.frequencyTypeID = request.json.get("frequencyTypeID")
    associations.fees = request.json.get("fees")
    associations.initiationFees = request.json.get("initiationFees")
    associations.communityMaintenance = request.json.get("communityMaintenance")
    associations.notes = request.json.get("notes")

    # Update associations in DB
    db.session.commit()

    # Return associations as json
    return associations.as_dict()

@app.route("/api/associations", methods=["POST", "OPTIONS"])
def createAssociations():
    print(request.json)
        
    # Create new associations class
    newAssociations = Associations()
    newAssociations.householdID = request.json.get("householdId")
    newAssociations.associationTypeID = request.json.get("associationTypeID")
    newAssociations.frequencyTypeID = request.json.get("frequencyTypeID")
    newAssociations.fees = request.json.get("fees")
    newAssociations.initiationFees = request.json.get("initiationFees")
    newAssociations.communityMaintenance = request.json.get("communityMaintenance")
    newAssociations.notes = request.json.get("notes")

    # Add associations to DB
    db.session.add(newAssociations)
    db.session.commit()

    # Return associations as json
    return newAssociations.as_dict()

############################## ROOF ROUTES ##############################

@app.route("/api/roof", methods=["GET", "OPTIONS"])
def getRoof():
    print("ARGS: " +str(request.args))

    householdId = request.args.get("householdId")
        
    # Get roof by id
    # query by house id, if result set has a row, return row. else, return empty {}

    roofRowCount = Roof.query.filter(Roof.id == householdId).count()

    if roofRowCount > 0:
        roof = Roof.query.filter(Roof.id == householdId).one()
        return roof.as_dict()

    # Return roof as json
    return ""

@app.route("/api/roof", methods=["PATCH", "OPTIONS"])
def updateRoof():
    print(request.json)
    householdId = request.json.get("id")
         
    # Get roof by id
    roof = Roof.query.filter(Roof.id == householdId).one()
    
    # Update roof class
    roof.householdID = request.json.get("householdId")
    roof.installationDate = request.json.get("installationDate")
    roof.invoicePhoto = request.json.get("invoicePhoto")
    roof.hasBeenReplaced = request.json.get("hasBeenReplaced")
    roof.hadExistingMaterialRemoved = request.json.get("hadExistingMaterialRemoved")
    roof.hasPreexistingLeaks = request.json.get("hasPreexistingLeaks")
    roof.hasRainwaterProblems = request.json.get("hasRainwaterProblems")
    roof.notes = request.json.get("notes")

    # Update roof in DB
    db.session.commit()

    # Return roof as json
    return roof.as_dict()

@app.route("/api/roof", methods=["POST", "OPTIONS"])
def createRoof():
    print(request.json)
        
    # Create new roof class
    newRoof = Roof()
    newRoof.householdID = request.json.get("householdId")
    newRoof.installationDate = request.json.get("installationDate")
    newRoof.invoicePhoto = request.json.get("invoicePhoto")
    newRoof.hasBeenReplaced = request.json.get("hasBeenReplaced")
    newRoof.hadExistingMaterialRemoved = request.json.get("hadExistingMaterialRemoved")
    newRoof.hasPreexistingLeaks = request.json.get("hasPreexistingLeaks")
    newRoof.hasRainwaterProblems = request.json.get("hasRainwaterProblems")
    newRoof.notes = request.json.get("notes")

    # Add roof to DB
    db.session.add(newRoof)
    db.session.commit()

    # Return roof as json
    return newRoof.as_dict()

############################## BASEMENT ROUTES ##############################

@app.route("/api/basement", methods=["GET", "OPTIONS"])
def getBasement():
    print("ARGS: " +str(request.args))

    householdId = request.args.get("householdId")
        
    # Get basement by id
    # query by house id, if result set has a row, return row. else, return empty {}

    basementRowCount = Roof.query.filter(Basement.id == householdId).count()

    if basementRowCount > 0:
        basement = Basement.query.filter(Basement.id == householdId).one()
        return basement.as_dict()

    # Return basement as json
    return ""

@app.route("/api/basement", methods=["PATCH", "OPTIONS"])
def updateBasement():
    print(request.json)
    householdId = request.json.get("id")
         
    # Get basement by id
    basement = Basement.query.filter(Basement.id == householdId).one()
    
    # Update roof class
    basement.householdID = request.json.get("householdId")
    basement.hasSumpPump = request.json.get("hasSumpPump")
    basement.pumpCount = request.json.get("pumpCount")
    basement.hasBeenUsed = request.json.get("hasBeenUsed")
    basement.hasWaterDamage = request.json.get("hasWaterDamage")
    basement.hasRepairs = request.json.get("hasRepairs")
    basement.hasDownspoutConnection = request.json.get("hasDownspoutConnection")
    basement.notes = request.json.get("notes")

    # Update basement in DB
    db.session.commit()

    # Return basement as json
    return basement.as_dict()

@app.route("/api/basement", methods=["POST", "OPTIONS"])
def createBsement():
    print(request.json)
        
    # Create new basement class
    newBasement = Basement()
    newBasement.householdID = request.json.get("householdId")
    newBasement.hasSumpPump = request.json.get("hasSumpPump")
    newBasement.pumpCount = request.json.get("pumpCount")
    newBasement.hasBeenUsed = request.json.get("hasBeenUsed")
    newBasement.hasWaterDamage = request.json.get("hasWaterDamage")
    newBasement.hasRepairs = request.json.get("hasRepairs")
    newBasement.hasDownspoutConnection = request.json.get("hasDownspoutConnection")
    newBasement.notes = request.json.get("notes")

    # Add bsement to DB
    db.session.add(newBasement)
    db.session.commit()

    # Return basement as json
    return newBasement.as_dict()

############################## LOOKUP ROUTES ##############################

@app.route("/api/roleType", methods=["GET", "OPTIONS"])
def getRoleType():
    print("ARGS: " +str(request.args))

    roleTypeID = request.args.get("roleTypeId")
        
    # Get roleType by id

    roleType = RoleType.query.filter(RoleType.id == roleTypeID).one()

    return roleType.as_dict()

@app.route("/api/frequencyType", methods=["GET", "OPTIONS"])
def getFrequencyType():
    print("ARGS: " +str(request.args))

    frequencyTypeID = request.args.get("frequencyTypeId")
        
    # Get frequencyType by id

    frequencyType = FrequencyType.query.filter(FrequencyType.id == frequencyTypeID).one()

    return frequencyType.as_dict()

@app.route("/api/associationType", methods=["GET", "OPTIONS"])
def getAssociationType():
    print("ARGS: " +str(request.args))

    associationTypeID = request.args.get("associationTypeId")
        
    # Get associationType by id

    associationType = AssociationType.query.filter(AssociationType.id == associationTypeID).one()

    return associationType.as_dict()
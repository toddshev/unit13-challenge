### Required Libraries ###
from datetime import datetime
from dateutil.relativedelta import relativedelta

### Functionality Helper Functions ###
def parse_int(n):
    """
    Securely converts a non-integer value to integer.
    """
    try:
        return int(n)
    except ValueError:
        return float("nan")


def build_validation_result(is_valid, violated_slot, message_content):
    """
    Define a result message structured as Lex response.
    """
    if message_content is None:
        return {"isValid": is_valid, "violatedSlot": violated_slot}

    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }


### Dialog Actions Helper Functions ###
def get_slots(intent_request):
    """
    Fetch all the slots and their values from the current intent.
    """
    return intent_request["currentIntent"]["slots"]


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Defines an elicit slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitSlot",
            "intentName": intent_name,
            "slots": slots,
            "slotToElicit": slot_to_elicit,
            "message": message,
        },
    }


def delegate(session_attributes, slots):
    """
    Defines a delegate slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {"type": "Delegate", "slots": slots},
    }


def close(session_attributes, fulfillment_state, message):
    """
    Defines a close slot type response.
    """

    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }

    return response

def validate_data(age, ia, intent_request):
    """
    Validate age and investment amount.  Other values are strings.
    """
    if age is not None:
        age = parse_int(age)
        if age < 0 or age > 65:
            return build_validation_result(
                False,
                "age",
                "You must be under 65 years old. Please try again.",
            )
    if ia is not None:
        ia = parse_int(ia)
        if ia <5000:
            return build_validation_result(
                False,
                "investmentAmount",
                "Sorry, must be at least $5,000",
            )
    return build_validation_result(True,None,None)


def build_recommendation(age, investment_amount, risk):
    age = parse_int(age)
    investment_amount = parse_int(investment_amount)
    reco_list = ["100% bonds (AGG), 0% equities (SPY)",
                "80% bonds (AGG), 20% equities (SPY)",
                "60% bonds (AGG), 40% equities (SPY)",
                "40% bonds (AGG), 60% equities (SPY)",
                "20% bonds (AGG), 80% equities (SPY)",
                "10% bonds (AGG), 90% equities (SPY)"]
    
    #Reco first based on risk, notch up 1 if age is less than 35
    if risk == 'vLow':
        initial = reco_list[0]
        if age <35:
            initial = reco_list[1] 
    elif risk == 'Low':
        initial = reco_list[1]
        if age < 35:
            initial = reco_list[2]
    elif risk == 'Medium':
        initial = reco_list[2]
        if age < 35:
            initial = reco_list[3]
    elif risk == 'High':
        initial = reco_list[3]
        if age < 35:
            initial = reco_list[4]
    else:
        initial = reco_list[4]
        if age <35:
            initial = reco_list[5]

    #Additional advice if large IA
    if investment_amount > 100000:
        initial +=  ".  However, due to your large initial investment, " \
                    "you may be able to take on more risk."
    return initial


### Intents Handlers ###
def recommend_portfolio(intent_request):
    """
    Performs dialog management and fulfillment for recommending a portfolio.
    """

    first_name = get_slots(intent_request)["firstName"]
    age = get_slots(intent_request)["age"]
    investment_amount = get_slots(intent_request)["investmentAmount"]
    risk_level = get_slots(intent_request)["riskLevel"]
    source = intent_request["invocationSource"]

    if source == "DialogCodeHook":
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt
        # for the first violation detected.
     
        ### YOUR DATA VALIDATION CODE STARTS HERE ###
        slots = get_slots(intent_request)
        
        validation_result = validate_data(age, investment_amount, intent_request)
        
        if not validation_result["isValid"]:
            slots[validation_result["violatedSlot"]] = None
        
            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
            )    

        
        ### YOUR DATA VALIDATION CODE ENDS HERE ###

        # Fetch current session attibutes
        output_session_attributes = intent_request["sessionAttributes"]

        return delegate(output_session_attributes, get_slots(intent_request))

    # Get the initial investment recommendation
    initial_recommendation = build_recommendation(age, investment_amount, risk_level)

    
    ### YOUR FINAL INVESTMENT RECOMMENDATION CODE STARTS HERE ###

    ### YOUR FINAL INVESTMENT RECOMMENDATION CODE ENDS HERE ###

    # Return a message with the initial recommendation based on the risk level.
    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": """{}, thank you for your information;
            based on the risk level you defined as well as your age of {}, my recommendation is to choose an investment portfolio with {}
            """.format(
                first_name, age, initial_recommendation
            ),
        },
    )


### Intents Dispatcher ###
def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    intent_name = intent_request["currentIntent"]["name"]

    # Dispatch to bot's intent handlers
    if intent_name == "RecommendPortfolio":
        return recommend_portfolio(intent_request)

    raise Exception("Intent with name " + intent_name + " not supported")


### Main Handler ###
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    
    return dispatch(event)


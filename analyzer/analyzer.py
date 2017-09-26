import os
import re
import logging

logger = logging.getLogger('faxlog.analyzer')

lastState = currentState = "FAX_IDLE"

eventModuleMap = {"Iwu_en_callmgntDataCallModifyInd":"CM",
        "Iwu_en_callmgntDataCallModifyRsp":"CM",
        "Iwu_en_vbdstate_change_resp":"SipWrapper",
        "Iwu_en_FaxTone_DetectInd":"SipWrapper",
        "Iwu_en_payloadTypeChange":"SipWrapper",
        "Iwu_en_T38BackVoiceTimeout":"CM"}

stateModuleMap = {"FaxccCallState_FaxIdle":"FAX_IDLE",
        "FaxccCallState_T38_DATA_CALL_INITIATED":"T38_INITIATED",
        "FaxccCallState_T38_DATA_CALL_ACTIVATED":"T38_ACTIVATED",
        "FaxccCallState_VBD_DATA_CALL_INITIATED":"VBD_INITIATED",
        "FaxccCallState_VBD_DATA_CALL_ACTIVATED":"VBD_ACTIVATED",
        "FaxccCallState_VOICE_DATA_CALL_INITIATED":"VOICE_INITIATED"}

mg_vbd_state_et = {"0":"STATE_VOICE",
        "1":"STATE_VBD","2":"STATE_NO_CHANGE"}

mg_ec_state_et = {"0":"ON","1":"OFF","2":"NO_CHANGE"}

mg_ec_switch = {"0":"EC_ON","1":"EC_OFF"}

Iwu_ty_dataCallState = {"-1":"INVALID","0":"VOICE","1":"VBD","2":"T38","3":"VOICE_INITIATED"}

Iwu_mm_Voice_Vbd_Switch_Type ={"0":"LOCAL_TONE_SWITCH","1":"PAYLOAD_TYPE_CHANGE_SWITCH"}

Iwu_ty_toneTypeDetected = {
        "0":"Iwu_en_cngToneOnScn",
        "1":"Iwu_en_cngToneOnPdn",
        "2":"Iwu_en_ansToneOnScn",
        "3":"Iwu_en_ansToneOnPdn",
        "4":"Iwu_en_v21PrembleOnScn",
        "5":"Iwu_en_v21PrembleOnPdn",
        "6":"Iwu_en_v21PrembleOnScn_remote",
        "7":"Iwu_en_v21PrembleOnPdn_remote",
        "8":"Iwu_en_faxeof",
        "9":"Iwu_en_normalVBDOnScn",
        "10":"Iwu_en_normalVBDOnPdn",
        "11":"Iwu_en_VBDECOffOnScn",
        "12":"Iwu_en_VBDECOffOnPdn",
        "13":"Iwu_en_holdingVBDOnScn",
        "14":"Iwu_en_holdingVBDOnPdn",
        "15":"Iwu_en_invalidTone"}

Iwu_ty_bool = {"0":"false","1":"true"}

Iwu_ty_vbd_mode = {
        "1":"AutoSwitch",
        "2":"Renegotiation",
        "3":"V152_FB_AutoSwitch",
        "4":"V152_FB_Renego",
        "5":"Reneg_CT_Mode"
        }

def EnumInt2Str(line):
    try:
        matchObj = re.search('(dIsV152NegoSucc=)(?P<dIsV152NegoSucc>\d*)',line)
        if matchObj:
            line = re.sub(matchObj.group(0), matchObj.group(1)+Iwu_ty_bool[matchObj.group(2)], line)

        matchObj = re.search('(gVbdMode=)(?P<gVbdMode>\d*)',line)
        if matchObj:
            line = re.sub(matchObj.group(0), matchObj.group(1)+Iwu_ty_vbd_mode[matchObj.group(2)], line)

        matchObj = re.search('(lIsSendVBDChangedReq=)(?P<lIsSendVBDChangedReq>\d*)',line)
        if matchObj:
            line = re.sub(matchObj.group(0), matchObj.group(1)+Iwu_ty_bool[matchObj.group(2)], line)

        matchObj = re.search('(lIsSendECChangedReq=)(?P<lIsSendECChangedReq>\d*)',line)
        if matchObj:
            line = re.sub(matchObj.group(0), matchObj.group(1)+Iwu_ty_bool[matchObj.group(2)], line)

        matchObj = re.search('(dToneTypeDetected=)(\d*)',line)
        if matchObj:
            line = re.sub(matchObj.group(0),matchObj.group(1)+Iwu_ty_toneTypeDetected[matchObj.group(2)],line)

        matchObj = re.search('(dVBDState=)(\d*)',line)
        if matchObj:
            line = re.sub(matchObj.group(0),matchObj.group(1)+mg_vbd_state_et[matchObj.group(2)],line)

        matchObj = re.search('(dECState=)(\d*)',line)
        if matchObj:
            line = re.sub(matchObj.group(0),matchObj.group(1)+mg_ec_state_et[matchObj.group(2)],line)

        matchObj = re.search('(dDataCallState=)(\d*)',line)
        if matchObj:
            line = re.sub(matchObj.group(0),matchObj.group(1)+Iwu_ty_dataCallState[matchObj.group(2)],line)
    except Exception as e:
        logger.error(repr(e))
    return line


"""
hanle the iwu_fn_ccFaxIdle line
"""
def handleIdleLine(line):
    logger.info("line is:"+line)
    try:
        matchObj = re.search('Enter FAX FSM.*event=(.*),CallId=(\d*)',line)
        if matchObj:
            event = matchObj.group(1)
            callid = matchObj.group(2)
            module = eventModuleMap[event]
            logger.info("event:"+event+",callid:"+callid+",module:"+module)
            stateLine = module + "->FAX_IDLE"
            a = stateLine + ":" + event + "\n" + "Note over FAX_IDLE:" + "CallId=" + matchObj.group(2) + "\n"
        else:
            matchObj = re.search('Leave FAX FSM\]current state=(\w*)',line)
            if matchObj:
                currentState = matchObj.group(1)
                module = stateModuleMap[currentState]
                a = "FAX_IDLE->" + module + ":change state to " + module + "\n"
            else:
                matchObj = re.search("iwu_fn_sendChangeVBDModel",line)
                if matchObj:
                    a = re.sub('\[iwu_fn_ccFaxIdle, \d*\]', "FAX_IDLE->SipWrapper",line)
                    a = EnumInt2Str(a)
                else:
                    a = re.sub('\[iwu_fn_ccFaxIdle, \d*\]', "Note over FAX_IDLE",line)
                    a = EnumInt2Str(a)
    except Exception as e:
        logger.error(repr(e))

    return a

"""
hanle the iwu_fn_ccVBDDataCallInitiated line
"""
def handleVBDInitiatedLine(line):
    try:
        matchObj = re.search('Enter FAX FSM.*event=(.*),CallId=(\d*)',line)
        if matchObj:
            event = matchObj.group(1)
            callid = matchObj.group(2)
            module = eventModuleMap[event]
            stateLine = module + "->VBD_INITIATED"
            a = stateLine + ":" + event + "\n" + "Note over VBD_INITIATED:" + "CallId=" + matchObj.group(2) + "\n"
        else:
            matchObj = re.search('Leave FAX FSM\]current state=(\w*)',line)
            if matchObj:
                currentState = matchObj.group(1)
                module = stateModuleMap[currentState]
                a = "VBD_INITIATED->" + module + ":change state to " + module + "\n"
            else:
                a = re.sub('\[iwu_fn_ccVBDDataCallInitiated, \d*\]', "Note over VBD_INITIATED",line)
                a = EnumInt2Str(a)
    except Exception as e:
        logger.error(repr(e))

    return a


"""
hanle the iwu_fn_ccVBDDataCallActivated line
"""
def handleVBDActivatedLine(line):
    try:
        matchObj = re.search('Enter FAX FSM.*event=(.*),CallId=(\d*)',line)
        if matchObj:
            event = matchObj.group(1)
            callid = matchObj.group(2)
            module = eventModuleMap[event]
            stateLine = module + "->VBD_ACTIVATED"
            a = stateLine + ":" + event + "\n" + "Note over VBD_ACTIVATED:" + "CallId=" + matchObj.group(2) + "\n"
        else:
            matchObj = re.search('Leave FAX FSM\]current state=(\w*)',line)
            if matchObj:
                currentState = matchObj.group(1)
                module = stateModuleMap[currentState]
                a = "VBD_ACTIVATED->" + module + ":change state to " + module + "\n"
            else:
                a = re.sub('\[iwu_fn_ccVBDDataCallActivated, \d*\]', "Note over VBD_ACTIVATED",line)
                a = EnumInt2Str(a)
    except Exception as e:
        logger.error(repr(e))
    return a


"""
hanle the iwu_fn_ccT38DataCallInitiated line
"""
def handleT38InitiatedLine(line):
    try:
        matchObj = re.search('Enter FAX FSM.*event=(.*),CallId=(\d*)',line)
        if matchObj:
            event = matchObj.group(1)
            callid = matchObj.group(2)
            module = eventModuleMap[event]
            stateLine = module + "->T38_INITIATED"
            a = stateLine + ":" + event + "\n" + "Note over T38_INITIATED:" + "CallId=" + matchObj.group(2) + "\n"
        else:
            matchObj = re.search('Leave FAX FSM\]current state=(\w*)',line)
            if matchObj:
                currentState = matchObj.group(1)
                module = stateModuleMap[currentState]
                a = "T38_INITIATED->" + module + ":change state to " + module + "\n"
            else:
                a = re.sub('\[iwu_fn_ccT38DataCallInitiated, \d*\]', "Note over T38_INITIATED",line)
                a = EnumInt2Str(a)
    except Exception as e:
        logger.error(repr(e))
    return a


"""
hanle the iwu_fn_ccT38DataCallActivated line
"""
def handleT38ActivatedLine(line):
    try:
        matchObj = re.search('Enter FAX FSM.*event=(.*),CallId=(\d*)',line)
        if matchObj:
            event = matchObj.group(1)
            callid = matchObj.group(2)
            module = eventModuleMap[event]
            stateLine = module + "->T38_ACTIVATED"
            a = stateLine + ":" + event + "\n" + "Note over T38_ACTIVATED:" + "CallId=" + matchObj.group(2) + "\n"
        else:
            matchObj = re.search('Leave FAX FSM\]current state=(\w*)',line)
            if matchObj:
                currentState = matchObj.group(1)
                module = stateModuleMap[currentState]
                a = "T38_ACTIVATED->" + module + ":change state to " + module + "\n"
            else:
                a = re.sub('\[iwu_fn_ccT38DataCallActivated, \d*\]', "Note over T38_ACTIVATED",line)
                a = EnumInt2Str(a)
    except Exception as e:
        logger.error(repr(e))
    return a


pattern = re.compile('\[iwu_fn_ccFaxIdle|\[iwu_fn_ccVBDDataCallInitiated| \
        \[iwu_fn_ccVBDDataCallActivated|\[iwu_fn_ccT38DataCallInitiated| \
        \[iwu_fn_ccT38DataCallActivated|\[iwu_fn_ccVoiceDataCallInitiated')


def analyze(logfile):
    try:
        with open(logfile+"_analyzed",'w') as wf:
            with open(logfile,'r') as f:
                for line in f.readlines():
                    matchObj = re.match('\[iwu_fn_ccFaxIdle', line)
                    if matchObj:
                        currentState = 'FAX_IDLE'
                        IdleLine = handleIdleLine(line)
                        wf.write(IdleLine)
                        continue
                        
                    matchObj = re.match('\[iwu_fn_ccVBDDataCallInitiated', line)
                    if matchObj:
                        VBDInitiatedLine = handleVBDInitiatedLine(line)
                        wf.write(VBDInitiatedLine)
                        continue

                    matchObj = re.match('\[iwu_fn_ccVBDDataCallActivated', line)
                    if matchObj:
                        VBDActivatedLine = handleVBDActivatedLine(line)
                        wf.write(VBDActivatedLine)
                        continue

                    matchObj = re.match('\[iwu_fn_ccT38DataCallInitiated', line)
                    if matchObj:
                        T38InitiatedLine = handleT38InitiatedLine(line)
                        wf.write(T38InitiatedLine)
                        continue

                    matchObj = re.match('\[iwu_fn_ccT38DataCallActivated', line)
                    if matchObj:
                        T38ActivateLine = handleT38ActivatedLine(line)
                        wf.write(T38ActivateLine)
                        continue
    except Exception as e:
        logger.error(repr(e))


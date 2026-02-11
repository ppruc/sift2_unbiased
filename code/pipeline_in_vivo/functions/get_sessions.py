import os

def get_sessions(dir, sub):
    sessions = os.listdir(os.path.join(dir, sub))
    sessions = [session for session in sessions if 'ses-' in session and session != 'ses-average']
    
    if "HCP" in dir:
        order = ["ses-test","ses-retest"]

        
    elif "Developing" in dir:
        order = ["ses-s1Bx1","ses-s1Bx2","ses-s1Bx3"]
        
    elif "Surgery" in dir:
        order = [
            "ses-baseline",
            "ses-followup",
            "ses-sixmonth",
            "ses-oneyear",
            "ses-twoyear",
            "ses-threeyear",
            "ses-retest"
            ]
    else:
        print("session order could not be determined")
            
    sorted_sessions = sorted(sessions, key=lambda x: order.index(x))
    sorted_sessions = sorted_sessions[:2]
    
    return sorted_sessions

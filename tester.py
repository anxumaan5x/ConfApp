from app import db, Chat, User
from datetime import datetime
import timedelta

def get_chats(from_id='112342845020655906267', to_id='1424567895645321456545'):
    timenow = datetime.now()
# # printing initial_date
# print (ini_time_for_now)
    
    my_list=[from_id, to_id]
    reversed_list=my_list
    reversed_list.reverse()
    # my_dict={{}}
    chats_dict={}
    get_chat=Chat.query.filter(Chat.from_id.in_(my_list),Chat.to_id.in_(reversed_list)).order_by(Chat.time.asc()).all()
    index=0
    for chat in get_chat:
        chats_dict[index]={}
        # print(f'{chat.message}, Sender = {chat.user.name}, time = {chat.time}')
        td = timedelta.Timedelta(timenow - chat.time)
        if td.total.hours<1:
            chats_dict[index]["timestamp"]=str(td.total.seconds) + ' seconds '
        elif td.total.hours<24:
            chats_dict[index]["timestamp"]=str(td.total.hours) + ' hour '
        else:
            chats_dict[index]["timestamp"]=str(td.total.days) + ' days '
        chats_dict[index]["sender"] = chat.from_id
        chats_dict[index]["message"] = chat.message   
        index=index+1  
    return chats_dict
    # print(chats_dict)
    


#get all chats for one user
def all_chats(to_id='112342845020655906267'):
    get_chat=Chat.query.filter_by(to_id=to_id).group_by(Chat.from_id).all()
    my_dict={}
    user_received_chats_from=[]
    # print(get_chat)
    for chat in get_chat:
        user_received_chats_from.append(chat.from_id)
    for sender in user_received_chats_from:
        # print(f'Chats between {to_id} and {sender}')
        my_dict[sender]=get_chats(sender, to_id)        
        print("")
    # print(my_dict)
    return my_dict
    print(user_received_chats_from)

# get_chats()
dictd=all_chats()
print(dictd)
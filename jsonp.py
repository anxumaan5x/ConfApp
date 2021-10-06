from datetime import datetime, timedelta
  
  
# Using current time
ini_time_for_now = datetime.utcnow()
# # printing initial_date
# print (ini_time_for_now)
  
old=(ini_time_for_now - timedelta(minutes = 15))
print((ini_time_for_now-old).seconds//60)
  
# future_date_after_2days = ini_time_for_now + \
#                          timedelta(days = 2)
  
# # printing calculated future_dates
# print('future_date_after_2yrs:', str(future_date_after_2yrs))
# print('future_date_after_2days:', str(future_date_after_2days))
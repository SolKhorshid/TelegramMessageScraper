import json
from datetime import date, datetime
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl.types import (
    PeerChannel
)
import api_info

danish_months = [
    "Januar",
    "Februar",
    "Marts",
    "April",
    "Maj",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "December",
]

# start_date = date(2022, 9, 13)
# end_date = date(2023, 2, 28)

start_date = date(2023, 3, 1)
end_date = date(2023, 9, 30)

# API information
api_id = api_info.api_id
api_hash = api_info.api_hash
phone = api_info.phone_number
username = api_info.username

# Create the client and connect
client = TelegramClient(username, api_id, api_hash)

async def main(phone):
    await client.start()
    print("Client Created")
    # Ensure you're authorized
    if await client.is_user_authorized() == False:
        await client.send_code_request(phone)
        try:
            await client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password: '))

    user_input_channel = input('enter entity(telegram URL or entity id):')

    if user_input_channel.isdigit():
        entity = PeerChannel(int(user_input_channel))
    else:
        entity = user_input_channel

    my_channel = await client.get_entity(entity)

    offset_id = 0
    limit = 100
    all_messages = []
    date_to_message: {date: [str]} = {}
    total_messages = 0
    total_count_limit = 0

    while True:
        print("Current Offset ID is:", offset_id, "; Total Messages:", total_messages)
        history = await client(GetHistoryRequest(
            peer=my_channel,
            offset_id=offset_id,
            offset_date = None,
            add_offset=0,
            limit=limit,
            max_id=0,
            min_id=0,
            hash=0
        ))
        if not history.messages:
            break
        messages = history.messages
        for message in messages:
            message_date = message.date.date()
            if message_date > end_date:
                continue
            if message_date < start_date:
                break
            
            if message.message in ["", None]:
                continue
            
            if message_date not in date_to_message:
                date_to_message[message_date] = [message.message]
            else:
                date_to_message[message_date].append(message.message)
        else:
            offset_id = messages[len(messages) - 1].id

            total_messages = len(all_messages)
            if total_count_limit != 0 and total_messages >= total_count_limit:
                break
            continue
        
        break

    print("Writing to JSON")
    with open('channel_messages.json', 'w') as outfile:
        formatted_dict = {str(key): value for key, value in date_to_message.items()} 
        json.dump(formatted_dict, outfile, ensure_ascii=False)
    
    for date in date_to_message.keys():
        messages = date_to_message[date]
        for index, message in enumerate(messages):
            # Format file name
            day_text = f"{date.day}" if date.day >= 10 else f"0{date.day}"
            month_text = f"{date.month}" if date.month >= 10 else f"0{date.month}"
            formatted_month = date.month + (12 * (date.year - 2022))
            formatted_month_text = f"{formatted_month}" if formatted_month >= 10 else f"0{formatted_month}"
            year_text = f"{date.year % 1000}"

            file_name = f"{formatted_month_text}_{day_text}{month_text}{year_text}_{index + 1}.txt"

            # Create folders
            data_folder_name = "scraped-data"
            if not os.path.exists(data_folder_name):
                os.makedirs(data_folder_name)

            folder_name = f"{date.year} - {danish_months[date.month - 1]}"
            folder_path = os.path.join(data_folder_name, folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            
            file_path = os.path.join(folder_path, file_name)
            
            with open(file_path, 'w') as file:
                file.write(message)
    
    return None

with client:
    client.loop.run_until_complete(main(phone))
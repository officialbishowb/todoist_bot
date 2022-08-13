import time
from dotenv import load_dotenv
load_dotenv()
import os
import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from todoist_api_python.api import TodoistAPI


API_TOKEN = os.getenv('BOT_TOKEN')
API = TodoistAPI(os.getenv('TODOIST_TOKEN'))
ACCESS_ID = os.getenv('ACCESS_ID').split(",") # User who can use the bot

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN,parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

##################################################################### BASIC COMMANDS #####################################################################
# To handle the basic two commands of this bot
@dp.message_handler(commands=['start','cmds'])
async def start_bot(message: types.Message):
    if str(message.from_user.id) in ACCESS_ID:
        if message.text.startswith('/start'):
            await message.reply(f'Hey, How are you doing <b>@{message.from_user.username}</b>?\n\nType /cmds to see all commands')
        elif message.text.startswith('/cmds'):
            await message.reply('/start - Start the bot\n/cmds - Show commands\n\n/add - Add a task\n/del - Delete a task\n/list - List all umcompleted tasks\n/enablereminder - Set reminders for a task')
    else:
        await message.reply('You are not authorized to use this bot')
    

##################################################################### MAIN COMMANDS #####################################################################
# To handle the main commands of this bot

# State for the add task command
class TaskAdd(StatesGroup):
    task_name = State()
    due_date = State()
    description = State()
    priority  = State()
    label = State()

# State for the del task command
class TaskDel(StatesGroup):
    task_id = State()
    
# List of message_id which should be deleted after adding a task or deleting a task
start_end_messageid = []
@dp.message_handler(commands=['add','del','list','enablereminder'])
async def bot_cmd_handler(message: types.Message):
    if message.text.startswith('/add'):
        
        
        start_end_messageid.append(message.message_id+1)
        #  Set state
        await TaskAdd.task_name.set()
        await message.reply('Note:  If you want to leave something empty, just type "No"')
        
        time.sleep(0.5)
        await message.reply('What is the name of the task?')
        
        
        
    elif message.text.startswith('/del'):
        
        start_end_messageid.append(message.message_id+1)
        #  Set state
        await TaskDel.task_id.set()
        await message.reply('What is the project id of the task? (Use /list command to view it)')
        
    elif message.text.startswith('/list'):
        tasks = await get_tasks()
        final_tasks = ""
        
        for task in tasks:
            # Get content variable from the Task object
            if not task.completed:
                final_tasks += f"""
<b>Task name: </b>{task.content}
<b>Created at: </b>{task.created}
<b>Description: </b> {task.description}
<b>Priority: </b> {define_priority(task.priority)}
<b>Task URL: </b> {task.url}
<b>Due date: </b> {task.due.date if task.due else ""}
<b>Task ID : </b> <code>{task.id}</code>
================="""
        await message.reply(final_tasks)
        
        
    elif message.text.startswith('/enablereminder'):
        print("ENABLEREMINDER")



############################################## DELETE TASK PROCESS FUNCTIONS ##############################################
@dp.message_handler(state=TaskDel.task_id)
async def process_name(message: types.Message, state: FSMContext):
    """
    Process task delete id
    """
    try:
        task_id = int(message.text)
    except ValueError:
        await message.reply("<b>Please enter a valid task id!</b>")
        await state.finish()
        return 
        
    try:
        API.delete_task(task_id=task_id)
        start_end_messageid.append(message.message_id+1)
        await bot.send_message(message.chat.id,"<b>Task deleted successfully!</b>")
    except Exception as error:
        await message.reply(f"Error: {error}")
        await state.finish()
    # Delete the message after adding a task or deleting a task
    await delete_messages(start_end_messageid[0],start_end_messageid[1],message.chat.id)
    start_end_messageid.clear()
        
    await state.finish()
        
    
############################################## ADD TASK PROCESS FUNCTIONS ##############################################

@dp.message_handler(state=TaskAdd.task_name)
async def process_name(message: types.Message, state: FSMContext):
    """
    Process task name
    """
    async with state.proxy() as task_add_data:
        task_add_data['task_name'] = message.text

    await TaskAdd.next()
    await message.reply("When is the task due? (example: tomorrow at 9pm, today)")
    
    
@dp.message_handler(state=TaskAdd.due_date)
async def process_task_due(message: types.Message, state: FSMContext):
    """
    Process task due date
    """
    async with state.proxy() as task_add_data:
        task_add_data['due_date'] = message.text

    await TaskAdd.next()
    await message.reply("Any description for the task?")
    

@dp.message_handler(state=TaskAdd.description)
async def process_task_description(message: types.Message, state: FSMContext):
    """
    Process task description
    """
    async with state.proxy() as task_add_data:
        task_add_data['description'] = message.text

    await TaskAdd.next()
    await message.reply("The priority of the task? (1-4)")
    
    
@dp.message_handler(state=TaskAdd.priority)
async def process_task_priority(message: types.Message, state: FSMContext):
    """
    Process task priority
    """
    async with state.proxy() as task_add_data:
        task_add_data['priority'] = message.text

    start_end_messageid.append(message.message_id+1)
    await bot.send_message(message.chat.id, "<b>Adding task...</b>")
    
    # Get all the data from the state
    valid_nones = ["No","no","nO","NO"]
    content = task_add_data['task_name'] if task_add_data['task_name'] not in valid_nones else ""
    due_date = task_add_data['due_date'] if task_add_data['due_date'] not in valid_nones else ""
    description = task_add_data['description'] if task_add_data['description'] not in valid_nones else ""
    priority = task_add_data['priority'] if task_add_data['priority'] not in valid_nones else ""
    
    # priority handeling
    try:
        priority = int(priority)
    except ValueError:
        priority = 4
    if priority > 4:
        priority = 4
        
    # Create task
    
    try:
        API.add_task(
            content=content,
            due_string = due_date,
            description = description,
            priority = priority,
        )
        time.sleep(1)
        await bot.edit_message_text("<b>Task added successfully!</b>\nView with /list", message.chat.id, message.message_id+1)
        # Delete all message related to add task command after adding the task beside the /add command and the last message
        await delete_messages(start_end_messageid[0],start_end_messageid[1],message.chat.id)
        start_end_messageid.clear()
    except Exception as e:
        await message.reply(f"Error: {e}")
        await state.finish()
        return
    
    await state.finish()
    
        
    
############################################## MAIN OTHER FUNCTIONS ##############################################

def define_priority(priority):
    
    """Set the priority of the task depending on the value of the priority variable
    Returns:
        string: the priority of the task
    """
    if priority == 1:
        return f"High ({str(priority)})"
    elif priority == 2:
        return f"Medium ({str(priority)})"
    elif priority == 3:
        return f"Low-Medium ({str(priority)})"
    elif priority == 4:
        return f"Low ({str(priority)})"
    else:
        return f"None ({str(priority)})"
    

async def get_tasks():
    """Get all the tasks

    Returns:
        Task - object: the tasks in a object format
    """
    try:
        tasks = API.get_tasks()
        return tasks
    except Exception as error:
        return error
    

async def delete_messages(start_range,end_range,chat_id):
    """Delete messages between two ranges

    Args:
        start_range (int): the starting range
        end_range (int): the end range
        chat_id (int): the chat id from which the messages will be deleted
    """
    
    for id in range(start_range,end_range):
        try:
            await bot.delete_message(chat_id,id)
        except:
            return False
    return True    


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
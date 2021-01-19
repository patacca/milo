#!/bin/env python3

import json, requests, sys, os, logging
from PIL import Image
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters

from config import TOKEN, LOG_FILE, SHARED_PATH, SHARED_URL

REQUEST_STATE = 0


def start(update, context):
	logger.debug(f'Chat {update.effective_chat.id}: started')
	update.message.reply_text(
		"Welcome to Milo, the helping bot for downloading manuscripts from DVL (The Digital Vatican Library)\n"
		"Write the link of the manuscript you want to download (example: https://digi.vatlib.it/view/MSS_Vat.ind.13)"
	)
	
	return REQUEST_STATE

def handleRequest(update, context):
	url = update.message.text
	logger.debug(f'Chat {update.effective_chat.id}: got a request for the url {url}')
	update.message.reply_text("Processing ...")
	
	r = requests.get(url)
	if not r.ok:
		logger.info(f'Chat {update.effective_chat.id}: url {url} returned HTTP {r.status_code}')
		update.message.reply_text('An error occurred while trying to download the required manuscript')
		return ConversationHandler.END
	
	manifest = json.loads(r.text)
	title = manifest['label']
	imagesUrl = [manifest['sequences'][0]['canvases'][k]['images'][0]['resource']['service']['@id'] for k in range(len(manifest['sequences'][0]['canvases']))]
	
	if not os.path.isdir('output'):
		os.mkdir('output')
	if not os.path.isdir(f'output/{title}'):
		os.mkdir(f'output/{title}')
	
	update.message.reply_text(f'Downloading {len(imagesUrl)} files ...')
	count = 0
	images = []
	for i in imagesUrl:
		if count % 30 == 0:
			update.message.reply_text(f'Processing number {count+1}/{len(imagesUrl)}')
		realUrl = i + '/full/full/0/native.jpg'
		r = requests.get(realUrl)
		if not r.ok:
			logger.info(f'Chat {update.effective_chat.id}: url {realUrl} returned HTTP {r.status_code}')
			update.message.reply_text('There was an error while trying to retrieve one page')
			return ConversationHandler.END
		
		f = open(f'output/{title}/{count}.jpg', 'wb')
		f.write(r.content)
		f.close()
		
		images.append(Image.open(f'output/{title}/{count}.jpg'))
		images[-1].convert('RGB')
		
		count += 1
	
	if len(images) > 0:
		images[0].save(f'output/{title}/{title}.pdf', save_all=True, append_images=images[1:])
	
	os.rename(f'output/{title}/{title}.pdf', f'{SHARED_PATH}/{title}.pdf')
	update.message.reply_text(f'{SHARED_URL}/{title}.pdf')
	
	return ConversationHandler.END

def cancel(update, context):
	logger.debug(f'Chat {update.effective_chat.id}: cancel conversation')
	update.message.reply_text('Bye!', reply_markup=ReplyKeyboardRemove())
	return ConversationHandler.END

if __name__ == '__main__':
	logger = logging.getLogger(__name__)
	logger.setLevel(logging.DEBUG)
	handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=1000*1000*1, backupCount=5)
	formatter = logging.Formatter('%(asctime)s - [%(levelname)s]  %(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	
	logger.info('Milo bot is starting')
	
	updater = Updater(token=TOKEN, use_context=True)
	dispatcher = updater.dispatcher
	
	conversationHandler = ConversationHandler(
		entry_points=[CommandHandler('start', start)],
		states={
			REQUEST_STATE: [MessageHandler(Filters.text & ~Filters.command, handleRequest)],
		},
		fallbacks=[CommandHandler('cancel', cancel)],
	)
	dispatcher.add_handler(conversationHandler)
	
	updater.start_polling()

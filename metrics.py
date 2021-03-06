import csv
from stanfordcorenlp import StanfordCoreNLP
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
import random
import re
import numpy as np
import tensorflow as tf
import tflearn

categories = ['spam', 'ham', 'info']
reader = csv.reader(open('training.csv', 'r'))
nlp = StanfordCoreNLP(r'C:\Program Files\Python36\stanford-corenlp-full-2017-06-09')

def tokenizer(sentence):
    temp = nlp.word_tokenize(sentence)
    temp1 = []
    for i in range(len(temp)):
        if(temp[i] in [',','.','?',';','!',':',"\"",'(',')','[',']','{','}',' ','\s','\\n']):
            continue
        elif(re.search(r'(\d+[/,-]\d+[/,-]\d+)',temp[i])):
            temp1.append("date")
        elif(re.search('\d+%', temp[i])):
            temp1.append("percentage")
        elif(re.match('\d+', temp[i])):
            temp1.append("number")
        elif(re.search('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', temp[i])):
            temp1.append("URL")
        else:
            temp1.append(temp[i])
    return temp1

lemmatizer = WordNetLemmatizer()
stopset = set(stopwords.words('english'))
docs = []
words = set()
lenmax = 0

testx = []
testy = []

lenmax = 0
for row in reader:
    lenmax += 1
    if(lenmax == 1):
        continue
    tokens = tokenizer(row[1])
    tokens = [lemmatizer.lemmatize(w.lower()) for w in tokens if w not in stopset]
    words.update(tokens)
    docs.append((tokens, row[0]))
    
words = sorted(words)

f = open("words.txt", "w")
f.write(' '.join(words))

training = []
op = []
op_empty = [0] * len(categories)

for doc in docs:
    bow = [0] * (len(words)+1)
    token_words = doc[0]
    for w in token_words:
        x = words.index(w)
        bow[x] = 1
    op_row = list(op_empty)
    op_row[categories.index(doc[1])] = 1
    training.append([bow, op_row])

random.shuffle(training)
training = np.array(training)


train_x = list(training[:,0])
train_y = list(training[:,1])

tf.reset_default_graph()

net = tflearn.input_data(shape=[None, len(train_x[0])])
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, 8, activation = 'softmax')
net = tflearn.fully_connected(net, len(train_y[0]), activation = 'sigmoid')
net = tflearn.regression(net)

model = tflearn.DNN(net, tensorboard_dir='tflearn_logs')
model.load("model.tflearn")
print("Model loaded...")

def get_tf(s_words):
    global words
    bow = [0]*(len(words)+1)
    for s in s_words:
        if s in words:
            x = words.index(s)
            bow[x] = 1
        else:
            bow[-1] = 1
    return(np.array(bow))

lenmax = 0
reader = csv.reader(open('test.csv', 'r'))
writer = csv.writer(open("answer.csv", 'w', newline = ''), delimiter = ',', quotechar = '|', quoting = csv.QUOTE_MINIMAL)
writer.writerow(["RecordNo", "Label"])
answer = []
print("Starting testing...")
for row in reader:
    lenmax += 1
    if(lenmax == 1):
        continue
    tokens = tokenizer(row[1])
    tokens = [lemmatizer.lemmatize(w.lower()) for w in tokens if w not in stopset]
    answer.append([lenmax-1, categories[np.argmax(model.predict([get_tf(tokens)]))]])
writer.writerows(answer)

metrics = model.evaluate(train_x, train_y, 10)
print("Evaluation metrics: \n", metrics)
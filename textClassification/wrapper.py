import os

import numpy as np

from textClassification.config import ModelConfig, TrainingConfig
from textClassification.models import getModel
from textClassification.models import train_model
from textClassification.models import train_folds
from textClassification.models import train_test_split
from textClassification.models import predict
from textClassification.preprocess import prepare_preprocessor, TextPreprocessor

from utilities.Embeddings import filter_embeddings

class Classifier(object):

    config_file = 'config.json'
    weight_file = 'model_weights.hdf5'
    preprocessor_file = 'preprocessor.pkl'

    def __init__(self, 
                 model_name="",
                 model_type="gru",
                 char_emb_size=25, 
                 word_emb_size=300, 
                 #char_lstm_units=25,
                 #word_lstm_units=100, 
                 dropout=0.5, 
                 use_char_feature=False, 
                 batch_size=20, 
                 optimizer='adam', 
                 learning_rate=0.001, 
                 lr_decay=0.9,
                 clip_gradients=5.0, 
                 max_epoch=50, 
                 patience=5,
                 max_checkpoints_to_keep=5, 
                 log_dir=None,
                 maxlen=300,
                 embeddings=()):

        self.model_config = ModelConfig(model_name, model_type, char_emb_size, word_emb_size, dropout, use_char_feature, maxlen)
        self.training_config = TrainingConfig(batch_size, optimizer, learning_rate,
                                              lr_decay, clip_gradients, max_epoch,
                                              patience, 
                                              max_checkpoints_to_keep)
        self.model = None
        self.models = None
        self.p = None
        self.log_dir = log_dir
        self.embeddings = embeddings 

    def train(self, x_train, y_train, vocab_init=None):
        #self.p = prepare_preprocessor(x_train, y_train, vocab_init=vocab_init)
        #embeddings = filter_embeddings(self.embeddings, self.p.vocab_word,
        #                               self.model_config.word_embedding_size)
        #self.model_config.vocab_size = len(self.p.vocab_word)
        #self.model_config.char_vocab_size = len(self.p.vocab_char)

        #self.model = SeqLabelling(self.model_config, embeddings, len(self.p.vocab_tag))

        self.p = prepare_preprocessor(x_train, vocab_init)

        embeddings = filter_embeddings(self.embeddings, self.p.vocab_word,
                                       self.model_config.word_embedding_size)

        x_train = self.p.to_sequence(x_train, self.model_config.maxlen)

        # create validation set in case we don't use k-folds
        xtr, val_x, y, val_y = train_test_split(x_train, y_train, test_size=0.1)

        self.model = getModel(self.model_config.model_type, embeddings)
        self.model, best_roc_auc = train_model(self.model, self.training_config.batch_size, 
            self.training_config.max_epoch, xtr, y, val_x, val_y)

        '''trainer = Trainer(self.model, 
                          self.models,
                          self.training_config,
                          checkpoint_path=self.log_dir,
                          preprocessor=self.p)
        trainer.train(x_train, y_train, x_valid, y_valid)'''

    def train_nfold(self, x_train, y_train, vocab_init=None, fold_number=10):

        self.p = prepare_preprocessor(x_train, vocab_init=vocab_init)

        embeddings = filter_embeddings(self.embeddings, self.p.vocab_word,
                                       self.model_config.word_embedding_size)

        xtr = self.p.to_sequence(x_train, self.model_config.maxlen)

        self.models = train_folds(xtr, y_train, args.fold_count, self.training_config.batch_size, 
            self.training_config.max_epoch, self.model_config.model_type, embeddings)

        '''
        self.p = prepare_preprocessor(x_train, y_train, vocab_init=vocab_init)
        embeddings = filter_embeddings(self.embeddings, self.p.vocab_word,
                                       self.model_config.word_embedding_size)
        self.model_config.vocab_size = len(self.p.vocab_word)
        self.model_config.char_vocab_size = len(self.p.vocab_char)

        for k in range(0,fold_number-1):
            self.model = SeqLabelling(self.model_config, embeddings, len(self.p.vocab_tag))
            self.models.append(model)

        trainer = Trainer(self.model, 
                          self.models,
                          self.training_config,
                          checkpoint_path=self.log_dir,
                          preprocessor=self.p)
        trainer.train_nfold(x_train, y_train, x_valid, y_valid)
        '''

    '''
    def eval(self, x_test, y_test):
        if self.model:
            evaluator = Evaluator(self.model, preprocessor=self.p)
            evaluator.eval(x_test, y_test)
        else:
            raise (OSError('Could not find a model. Call load(dir_path).'))
    '''

    # classification
    def predict(self, text):
        if self.model:
            #classifier = Classifier(self.model, preprocessor=self.p)
            x_t = self.model.p.to_sequence(text, maxlen=300)
            return self.model.predict(x_t)
        else:
            raise (OSError('Could not find a model. Call load(dir_path).'))

    # regression
    def predict_proba(self, text):
        if self.model:
            #classifier = Classifier(self.model, preprocessor=self.p)
            x_t = self.model.p.to_sequence(text, maxlen=300)
            #return self.model.predict_proba(x_t)
            return self.model.predict(x_t)
        else:
            raise (OSError('Could not find a model. Call load(dir_path).'))

    def save(self, dir_path='data/models/'):
        # create subfolder for the model if not already exists
        directory = os.path.join(dir_path, self.model_config.model_name)
        if not os.path.exists(directory):
            os.makedirs(directory)
        self.p.save(os.path.join(directory, self.preprocessor_file))
        print('preprocessor saved')
        self.model_config.save(os.path.join(directory, self.config_file))
        print('model config file saved')
        self.model.save(os.path.join(directory, self.weight_file))
        print('model saved')

    def load(self, dir_path='data/models/'):
        self.p = TextPreprocessor.load(os.path.join(dir_path, self.model_config.model_name, self.preprocessor_file))
        config = ModelConfig.load(os.path.join(dir_path, self.model_config.model_name, self.config_file))
        dummy_embeddings = np.zeros((config.vocab_size, config.word_embedding_size), dtype=np.float32)
        self.model = getModel(self.model_config.model_type, self.embeddings)
        self.model.load_weights(os.path.join(dir_path, self.model_config.model_name, self.weight_file))
        #self.model.load(filepath=os.path.join(dir_path, self.model_config.model_name, self.weight_file))



<img align="right" width="150" height="150" src="doc/cat-delft-small.jpg">

[![License](http://img.shields.io/:license-apache-blue.svg)](http://www.apache.org/licenses/LICENSE-2.0.html)

# DeLFT 


__Work in progress !__ 

__DeLFT__ (**De**ep **L**earning **F**ramework for **T**ext) is a Keras framework for text processing, covering sequence labelling (e.g. named entity tagging) and text classification (e.g. comment classification). This library re-implements standard state-of-the-art Deep Learning architectures. 

From the observation that most of the open source implementations using Keras are toy examples, our motivation is to develop a framework that can be efficient, scalable and more usable in a production environment (with all the known limitations of Python of course for this purpose). The benefits of DELFT are:

* Re-implement a variety of state-of-the-art deep learning architectures for both sequence labelling and text classification problems which can all be used within the same environment.

* Reduce model size, in particular by removing word embeddings from them. For instance, the model for the toxic comment classifier went down from a size of 230 MB with embeddings to 1.8 MB. In practice the size of all the models of DeLFT is less than 2 MB.

* Use dynamic data generator so that the training data do not need to stand completely in memory.

* Load and manage efficiently an unlimited volume of pre-trained embedding: instead of loading pre-trained embeddings in memory - which is horribly slow in Python and limit the number of embeddings to be used simultaneously - the pre-trained embeddings are compiled the first time they are accessed and stored efficiently in a LMDB database. This permits to have the pre-trained embeddings immediatly "warm" (no load time), to free memory and to use any number of embeddings with a very negligible impact on runtime when using SSD. 

The medium term goal is then to provide good performance (accuracy, runtime, compactness) models to a production stack such as Java/Scala and C++. 

DeLFT has been tested with python 3.5, Keras 2.1 and Tensorflow 1.7 as backend. At this stage, we do not garantee that DeLFT will run with other different versions of these library or other Keras backend versions. As always, GPU(s) are required for decent training time. 

## Install 

Get the github repo:

> git clone https://github.com/kermitt2/delft
> cd delft

It is advised to setup first a virtual environment to avoid falling into one of these gloomy python dependency marshlands:

> virtualenv --system-site-packages -p python3 env

> source env/bin/activate

Install the dependencies, if you have a GPU and CUDA (>=8.0) installed use:

> pip3 install -r requirements-gpu.txt

otherwise if you can use only your CPU:

> pip3 install -r requirements.txt

You need then to download some pre-trained word embeddings and notify their path into the embedding registry. We suggest for exploiting the provided models:

- _glove Common Crawl_ (2.2M vocab., cased, 300 dim. vectors): [glove-840B](http://nlp.stanford.edu/data/glove.840B.300d.zip) 

- _fasttext Common Crawl_ (2M vocab., ?, 300 dim. vectors): [fasttext-crawl](https://s3-us-west-1.amazonaws.com/fasttext-vectors/crawl-300d-2M.vec.zip) 

- _word2vec GoogleNews_ (3M vocab., ?, 300 dim. vectors): [word2vec](https://drive.google.com/file/d/0B7XkCwpI5KDYNlNUTTlSS21pQmM/edit?usp=sharing)

Then edit the file `embedding-registry.json` and modifiy the value for `path` according to the path where you have saved the corresponding embeddings. The embedding files must be unzipped.

```json
{
    "embeddings": [
        {
            "name": "glove-840B",
            "path": "/PATH/TO/THE/UNZIPPED/EMBEDDINGS/FILE/glove.840B.300d.txt",
            "type": "glove",
            "format": "vec", 
            "lang": "en",
            "item": "word"
        },
        ...
    ]
}

```

You're ready to use DeLFT. 

## Management of embeddings 

The first time DeLFT starts and accesses pre-trained embeddings, these embeddings are serialized and stored in a LMDB database, a very efficient embedded database using memory page (already used in the Machine Learning world by Caffe and Torch for managing large training data). The next time these embeddings will be accessed, they will be immediatly available. 

Our approach solves the bottleneck problem pointed for instance [here](https://spenai.org/bravepineapple/faster_em/) in a much better way than quantizing+compression or prunning. After being compiled and stored at the first access, any volume of embeddings vectors can be used immediatly without any loading, with a negligible usage of memory, without any accuracy loss and with a negligible impact on runtime when using SSD. 

For instance, in a traditional approach `glove-840B` takes around 2 minutes to load and 4GB in memory. Managed with LMDB, after a first load time of around 4 minutes, `glove-840B` can be accessed immediatly and takes only a couple MB in memory, for an impact on runtime negligible (around 1% slower) for any further command line calls.

By default, the LMDB databases are stored under the subdirectory `data/db`. The size of a database is roughly equivalent to the size of the original uncompressed embeddings file. To modify this path, edit the file `embedding-registry.json` and change the value of the attribute `embedding-lmdb-path`.

> I have plenty of memory on my machine, I don't care about load time because I need to grab a coffee, I only process one language at the time, so I am not interested in taking advantage of the LMDB emebedding management ! 

Ok, ok, then set the `embedding-lmdb-path` value to `"None"` in the file `embedding-registry.json`, the embeddings will be loaded in memory as immutable data, like in the usual Keras scripts. 


## Sequence Labelling

### Available models

- _BidLSTM-CRF_ with words and characters input following: 

[1] Guillaume Lample, Miguel Ballesteros, Sandeep Subramanian, Kazuya Kawakami, Chris Dyer. "Neural Architectures for Named Entity Recognition". Proceedings of NAACL 2016. https://arxiv.org/abs/1603.01360


- _BidLSTM-CNN_ with words, characters and custom casing features input following: 

[2] Jason P. C. Chiu, Eric Nichols. "Named Entity Recognition with Bidirectional LSTM-CNNs". 2016. https://arxiv.org/abs/1511.08308


- _BidLSTM-CNN-CRF_ with words, characters and custom casing features input following: 

[3] Xuezhe Ma and Eduard Hovy. "End-to-end Sequence Labeling via Bi-directional LSTM-CNNs-CRF". 2016. https://arxiv.org/abs/1603.01354


### Usage

...

### Examples

#### NER

DeLFT comes with a pre-trained model for the CoNLL-2003 NER dataset. By default, the BidLSTM-CRF model is used. With this available model, glove-840B word embeddings, the current f1 score on CoNLL 2003 _testb_ set is __91.09__ (using _train_ set for training and _testa_ for validation), as compared to the 90.94 reported in [1].

For re-training a model, assuming that the usual CoNLL-2003 NER dataset (`eng.train`, `eng.testa`, `eng.testb`) is present under `data/sequenceLabelling/CoNLL-2003/`, for training and evaluating use:

> python3 nerTagger.py train_eval

By default, the BidLSTM-CRF model is used. Documentation on selecting other models and setting hyperparameters to be included here !

For evaluating against CoNLL 2003 testb set with the existing model:

> python3 nerTagger.py eval

```
    Evaluation on test set:
        f1 (micro): 91.09

                 precision    recall  f1-score   support

            ORG     0.8879    0.8868    0.8873      1661
           MISC     0.8031    0.8248    0.8138       702
            LOC     0.9212    0.9317    0.9264      1668
            PER     0.9728    0.9518    0.9622      1617

    avg / total     0.9108    0.9109    0.9109      5648

```

For training with all the available data:

> python3 nerTagger.py train

You can also train multiple times with the n-folds options: the model will be trained n times with different seed values but with the same sets if the evaluation set is provided. The evaluation will then give the average scores over these n models (against test set) and for the best model which will be saved. For 10 times training for instance, use:

> python3 nerTagger.py train_eval --fold-count 10

After training a model, for tagging some text, use the command:

> python3 nerTagger.py tag

which produces a JSON output with entities, scores and character offsets like this:

```json
{
    "runtime": 0.34,
    "texts": [
        {
            "text": "The University of California has found that 40 percent of its students suffer food insecurity. At four state universities in Illinois, that number is 35 percent.",
            "entities": [
                {
                    "text": "University of California",
                    "endOffset": 32,
                    "score": 1.0,
                    "class": "ORG",
                    "beginOffset": 4
                },
                {
                    "text": "Illinois",
                    "endOffset": 134,
                    "score": 1.0,
                    "class": "LOC",
                    "beginOffset": 125
                }
            ]
        },
        {
            "text": "President Obama is not speaking anymore from the White House.",
            "entities": [
                {
                    "text": "Obama",
                    "endOffset": 18,
                    "score": 1.0,
                    "class": "PER",
                    "beginOffset": 10
                },
                {
                    "text": "White House",
                    "endOffset": 61,
                    "score": 1.0,
                    "class": "LOC",
                    "beginOffset": 49
                }
            ]
        }
    ],
    "software": "DeLFT",
    "date": "2018-05-02T12:24:55.529301",
    "model": "ner"
}

```
<p align="center">
    <img src="https://abstrusegoose.com/strips/muggle_problems.png">
</p>

This above work is licensed under a [Creative Commons Attribution-Noncommercial 3.0 United States License](http://creativecommons.org/licenses/by-nc/3.0/us/). 

#### GROBID models

DeLFT supports [GROBID](https://github.com/kermitt2/grobid) training data (originally for CRF) and GROBID feature matrix to be labelled. 

Train a model:

> python3 grobidTagger.py *name-of-model* train

where *name-of-model* is one of GROBID model (_date_, _affiliation-address_, _citation_, _header_, , _name-citation_, _name-header_, ...), for instance: 

> python3 grobidTagger.py date train

To segment the training data and eval on 10%:

> python3 grobidTagger.py *name-of-model* train_eval

For instance for the _date_ model:

> python3 grobidTagger.py date train_eval

```
        Evaluation:
        f1 (micro): 96.41
                 precision    recall  f1-score   support

        <month>     0.9667    0.9831    0.9748        59
         <year>     1.0000    0.9844    0.9921        64
          <day>     0.9091    0.9524    0.9302        42

    avg / total     0.9641    0.9758    0.9699       165
```

For applying a model on some examples: 

> python3 grobidTagger.py date tag

```
{
    "runtime": 0.509,
    "software": "DeLFT",
    "model": "grobid-date",
    "date": "2018-05-23T14:18:15.833959",
    "texts": [
        {
            "entities": [
                {
                    "score": 1.0,
                    "endOffset": 6,
                    "class": "<month>",
                    "beginOffset": 0,
                    "text": "January"
                },
                {
                    "score": 1.0,
                    "endOffset": 11,
                    "class": "<year>",
                    "beginOffset": 8,
                    "text": "2006"
                }
            ],
            "text": "January 2006"
        },
        {
            "entities": [
                {
                    "score": 1.0,
                    "endOffset": 4,
                    "class": "<month>",
                    "beginOffset": 0,
                    "text": "March"
                },
                {
                    "score": 1.0,
                    "endOffset": 13,
                    "class": "<day>",
                    "beginOffset": 10,
                    "text": "27th"
                },
                {
                    "score": 1.0,
                    "endOffset": 19,
                    "class": "<year>",
                    "beginOffset": 16,
                    "text": "2001"
                }
            ],
            "text": "March the 27th, 2001"
        }
    ]
}
```

(To be completed)

#### Insult recognition

A small experimental model for recognizing insults and threats in texts, based on the Wikipedia comment from the Kaggle _Wikipedia Toxic Comments_ dataset, English only. This uses a small dataset labelled manually. 

For training:

> python3 insultTagger.py train

By default training uses the whole train set.

Example of a small tagging test:

> python3 insultTagger.py tag

will produced (__socially offensive language warning!__) result like this: 

```json
{
    "runtime": 0.969,
    "texts": [
        {
            "entities": [],
            "text": "This is a gentle test."
        },
        {
            "entities": [
                {
                    "score": 1.0,
                    "endOffset": 20,
                    "class": "<insult>",
                    "beginOffset": 9,
                    "text": "moronic wimp"
                },
                {
                    "score": 1.0,
                    "endOffset": 56,
                    "class": "<threat>",
                    "beginOffset": 54,
                    "text": "die"
                }
            ],
            "text": "you're a moronic wimp who is too lazy to do research! die in hell !!"
        }
    ],
    "software": "DeLFT",
    "date": "2018-05-14T17:22:01.804050",
    "model": "insult"
}
```


#### Creating your own model

As long your task is a sequence labelling of text, adding a new corpus and create an additional model should be straightfoward. If you want to build a model named `toto` based on labelled data in one of the supported format (CoNLL, TEI or GROBID CRF), create the subdirectory `data/sequenceLabelling/toto` and copy your training data under it.  

(To be completed)

## Text classification

### Available models

All the following models includes Dropout, Pooling and Dense layers with hyperparameters tuned for reasonable performance across standard text classification tasks. If necessary, they are good basis for further performance tuning. 
 
* `gru`: two layers Bidirectional GRU
* `gru_simple`: one layer Bidirectional GRU
* `bidLstm`: a Bidirectional LSTM layer followed by an Attention layer
* `cnn`: convolutional layers followed by a GRU
* `lstm_cnn`: LSTM followed by convolutional layers
* `mix1`: one layer Bidirectional GRU followed by a Bidirectional LSTM
* `dpcnn`: Deep Pyramid Convolutional Neural Networks (but not working as expected - to be reviewed)

Note: by default the first 300 tokens of the text to be classified are used, which is largely enough for any _short text_ classification tasks and works fine with low profile GPU (for instance GeForce GTX 1050 with 4 GB memory). For taking into account a larger portion of the text, modify the config model parameter `maxlen`. However, using more than 1000 tokens for instance requires a modern GPU with enough memory (e.g. 10 GB). 

### Usage

...

### Examples

#### Toxic comment classification

The dataset of the [Kaggle Toxic Comment Classification challenge](https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge) can be found here: https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge/data

This is a multi-label regression problem, where a Wikipedia comment (or any similar short texts) should be associated to 6 possible types of toxicity (`toxic`, `severe_toxic`, `obscene`, `threat`, `insult`, `identity_hate`).

To launch the training: 

> python3 toxicCommentClassifier.py train

For training with n-folds, use the parameter `--fold-count`:

> python3 toxicCommentClassifier.py train --fold-count 10

After training (1 or n-folds), to process the Kaggle test set, use:

> python3 toxicCommentClassifier.py test

To classify a set of comments: 

> python3 toxicCommentClassifier.py classify


#### Twitter 

TBD

#### Citation classification

We use the dataset developed and presented by A. Athar in the following article:

[4] Awais Athar. "Sentiment Analysis of Citations using Sentence Structure-Based Features". Proceedings of the ACL 2011 Student Session, 81-87, 2011. http://www.aclweb.org/anthology/P11-3015

For a given scientific article, the task is to estimate if the occurrence of a bibliographical citation is positive, neutral or negative given its citation context. Note that the dataset, similarly to the Toxic Comment classification, is highly unbalanced (86% of the citations are neutral). 

In this example, we formulate the problem as a 3 class regression (`negative`. `neutral`, `positive`). To train the model:

> python3 citationClassifier.py train

with n-folds:

> python3 citationClassifier.py train --fold-count 10

Training and evalation (ratio):

> python3 citationClassifier.py train-eval

which should produce the following evaluation (using the 2-layers Bidirectional GRU model `gru`): 

<!-- eval before data generator
```
Evaluation on 896 instances:

Class: negative
    accuracy at 0.5 = 0.9665178571428571
    f-1 at 0.5 = 0.9665178571428571
    log-loss = 0.10193770380479757
    roc auc = 0.9085232470270055

Class: neutral
    accuracy at 0.5 = 0.8995535714285714
    f-1 at 0.5 = 0.8995535714285714
    log-loss = 0.2584601024897698
    roc auc = 0.8914776135848872

Class: positive
    accuracy at 0.5 = 0.9252232142857143
    f-1 at 0.5 = 0.9252232142857143
    log-loss = 0.20726886795593405
    roc auc = 0.8892779640954823

Macro-average:
    average accuracy at 0.5 = 0.9304315476190476
    average f-1 at 0.5 = 0.9304315476190476
    average log-loss = 0.18922222475016715
    average roc auc = 0.8964262749024584

Micro-average:
    average accuracy at 0.5 = 0.9304315476190482
    average f-1 at 0.5 = 0.9304315476190482
    average log-loss = 0.18922222475016712
    average roc auc = 0.9319196428571429
```    
-->


```
Evaluation on 896 instances:

Class: negative
    accuracy at 0.5 = 0.9654017857142857
    f-1 at 0.5 = 0.9654017857142857
    log-loss = 0.1056664130630102
    roc auc = 0.898580121703854

Class: neutral
    accuracy at 0.5 = 0.8939732142857143
    f-1 at 0.5 = 0.8939732142857143
    log-loss = 0.25354114470640177
    roc auc = 0.88643347739321

Class: positive
    accuracy at 0.5 = 0.9185267857142857
    f-1 at 0.5 = 0.9185267857142856
    log-loss = 0.1980544119553914
    roc auc = 0.8930591175116723

Macro-average:
    average accuracy at 0.5 = 0.9259672619047619
    average f-1 at 0.5 = 0.9259672619047619
    average log-loss = 0.18575398990826777
    average roc auc = 0.8926909055362455

Micro-average:
    average accuracy at 0.5 = 0.9259672619047624
    average f-1 at 0.5 = 0.9259672619047624
    average log-loss = 0.18575398990826741
    average roc auc = 0.9296875


```

In [4], based on a SVM (linear kernel) and custom features, the author reports a F-score of 0.898 for micro-average and 0.764 for macro-average. As we can observe, a non-linear deep learning approach, even without any feature engineering nor tuning, is very robust for an unbalanced dataset and provides higher accuracy.

To classify a set of citation contexts:

> python3 citationClassifier.py classify

which will produce some JSON output like this:

```json
{
    "model": "citations",
    "date": "2018-05-13T16:06:12.995944",
    "software": "DeLFT",
    "classifications": [
        {
            "negative": 0.001178970211185515,
            "text": "One successful strategy [15] computes the set-similarity involving (multi-word) keyphrases about the mentions and the entities, collected from the KG.",
            "neutral": 0.187219500541687,
            "positive": 0.8640883564949036
        },
        {
            "negative": 0.4590276777744293,
            "text": "Unfortunately, fewer than half of the OCs in the DAML02 OC catalog (Dias et al. 2002) are suitable for use with the isochrone-fitting method because of the lack of a prominent main sequence, in addition to an absence of radial velocity and proper-motion data.",
            "neutral": 0.3570767939090729,
            "positive": 0.18021513521671295
        },
        {
            "negative": 0.0726129561662674,
            "text": "However, we found that the pairwise approach LambdaMART [41] achieved the best performance on our datasets among most learning to rank algorithms.",
            "neutral": 0.12469841539859772,
            "positive": 0.8224021196365356
        }
    ],
    "runtime": 1.202
}


```


## TODO


__Embeddings__: 

* use/experiment OOV mechanisms

* support `.bin` FastText format

__Models__:

* Test Theano as alternative backend (waiting for Apache MXNet...)

* augment word vectors with features, in particular layout features generated by GROBID

__NER__:

* benchmark with OntoNotes 5 (English and other languages) and French NER

__Production stack__:

* see how efficiently feed and execute those Keras/Tensorflow models with DL4J/Java

__Build more models and examples__...

* e.g. POS tagger and dependency parser

## Acknowledgments

* Keras CRF implementation by Philipp Gross 

* The evaluations for sequence labelling are based on a modified version of https://github.com/chakki-works/seqeval

* The preprocessor of the sequence labelling part is derived from https://github.com/Hironsan/anago/

## License and contact

Distributed under [Apache 2.0 license](http://www.apache.org/licenses/LICENSE-2.0). 

Contact: Patrice Lopez (<patrice.lopez@science-miner.com>)


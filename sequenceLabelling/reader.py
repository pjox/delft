import numpy as np
import xml
from xml.sax import make_parser, handler
from utilities.Tokenizer import tokenizeAndFilterSimple
import re

class TEIContentHandler(xml.sax.ContentHandler):
    """ 
    TEI XML SAX handler for reading mixed content within xml text tags  
    """
    
    # local sentence
    tokens = []
    labels = []

    # all sentences of the document
    sents = []
    allLabels = []

    # working variables
    accumulated = ''
    currentLabel = None

    def __init__(self):
        xml.sax.ContentHandler.__init__(self)
     
    def startElement(self, name, attrs):
        if self.accumulated != '':
            localTokens = tokenizeAndFilterSimple(self.accumulated)
            for token in localTokens:
                self.tokens.append(token)
                self.labels.append('O')
        if name == 'TEI' or name == 'tei':
            # beginning of a document
            self.tokens = []
            self.labels = []
            self.sents = []
            self.allLabels = []
        if name == "p":
            # beginning of sentence
            self.tokens = []
            self.labels = []
            self.currentLabel = 'O'
        if name == "rs":
            # beginning of entity
            if attrs.getLength() != 0:
                if attrs.getValue("type") != 'insult' and attrs.getValue("type") != 'threat':
                    print("Invalid entity type:", attrs.getValue("type"))
                self.currentLabel = '<'+attrs.getValue("type")+'>'
        self.accumulated = ''
                
    def endElement(self, name):
        # print("endElement '" + name + "'")
        if name == "p":
            # end of sentence 
            if self.accumulated != '':
                localTokens = tokenizeAndFilterSimple(self.accumulated)
                for token in localTokens:
                    self.tokens.append(token)
                    self.labels.append('O')

            self.sents.append(self.tokens)
            self.allLabels.append(self.labels)
            tokens = []
            labels = []
        if name == "rs":
            # end of entity
            localTokens = tokenizeAndFilterSimple(self.accumulated)
            begin = True
            if self.currentLabel is None:
                self.currentLabel = 'O'
            for token in localTokens:
                self.tokens.append(token)
                if begin:
                    self.labels.append('B-'+self.currentLabel)
                    begin = False
                else:     
                    self.labels.append('I-'+self.currentLabel)
            self.currentLabel = None
        self.accumulated = ''
    
    def characters(self, content):
        self.accumulated += content
     
    def getSents(self):
        return np.asarray(self.sents)

    def getAllLabels(self):
        return np.asarray(self.allLabels)

    def clear(self): # clear the accumulator for re-use
        self.accumulated = ""


class ENAMEXContentHandler(xml.sax.ContentHandler):
    """ 
    ENAMEX-style XML SAX handler for reading mixed content within xml text tags  
    """
    
    # local sentence
    tokens = []
    labels = []

    # all sentences of the document
    sents = []
    allLabels = []

    # working variables
    accumulated = ''
    currentLabel = None
    corpus_type = ''

    def __init__(self, corpus_type='lemonde'):
        xml.sax.ContentHandler.__init__(self)
        self.corpus_type = corpus_type

    def translate_fr_labels(self, mainType, subType):
        #default
        labelOutput = "O"
        senseOutput = ""

        if mainType.lower() == "company":
            labelOutput = 'business'
        elif mainType.lower() == "fictioncharacter":
            labelOutput = "person"
        elif mainType.lower() == "organization": 
            if subType.lower() == "institutionalorganization":
                labelOutput = "institution"
            elif subType.lower() == "company":
                labelOutput = "business"
            else: 
                labelOutput = "organisation"
        elif mainType.lower() ==  "person":
            labelOutput = "person"
        elif mainType.lower() ==  "location":
            labelOutput = "location"
        elif mainType.lower() ==  "poi":
            labelOutput = "location"
        elif mainType.lower() ==  "product":
            labelOutput = "artifact"
        
        return labelOutput

    def startElement(self, name, attrs):
        if self.accumulated != '':
            localTokens = tokenizeAndFilterSimple(self.accumulated)
            for token in localTokens:
                self.tokens.append(token)
                self.labels.append('O')
        if name == 'corpus':
            # beginning of a document
            self.tokens = []
            self.labels = []
            self.sents = []
            self.allLabels = []
        if name == "sentence":
            # beginning of sentence
            self.tokens = []
            self.labels = []
            self.currentLabel = 'O'
        if name == "ENAMEX":
            # beginning of entity
            if attrs.getLength() != 0:
                #if attrs.getValue("type") != 'insult' and attrs.getValue("type") != 'threat':
                #    print("Invalid entity type:", attrs.getValue("type"))
                mainType = attrs.getValue("type")
                if "sub_type" in attrs:
                    subType = attrs.getValue("sub_type")
                else:
                    subType = ''
                if self.corpus_type == 'lemonde':
                    self.currentLabel = '<'+self.translate_fr_labels(mainType, subType)+'>'
                else:
                    self.currentLabel = '<'+attrs.getValue("type")+'>'
        self.accumulated = ''
                
    def endElement(self, name):
        #print("endElement '" + name + "'")
        if name == "sentence":
            # end of sentence 
            if self.accumulated != '':
                localTokens = tokenizeAndFilterSimple(self.accumulated)
                for token in localTokens:
                    self.tokens.append(token)
                    self.labels.append('O')

            self.sents.append(self.tokens)
            self.allLabels.append(self.labels)
            tokens = []
            labels = []
        if name == "ENAMEX":
            # end of entity
            localTokens = tokenizeAndFilterSimple(self.accumulated)
            begin = True
            if self.currentLabel is None:
                self.currentLabel = 'O'
            for token in localTokens:
                self.tokens.append(token)
                if begin:
                    self.labels.append('B-'+self.currentLabel)
                    begin = False
                else:     
                    self.labels.append('I-'+self.currentLabel)
            self.currentLabel = None
        self.accumulated = ''
    
    def characters(self, content):
        self.accumulated += content
     
    def getSents(self):
        return np.asarray(self.sents)

    def getAllLabels(self):
        return np.asarray(self.allLabels)

    def clear(self): # clear the accumulator for re-use
        self.accumulated = ""


def load_data_and_labels_xml_string(stringXml):
    """
    Load data and label from a string 
    the format is as follow:
    <p> 
        bla bla you are a <rs type="insult">CENSURED</rs>, 
        and I will <rs type="threat">find and kill</rs> you bla bla
    </p>
    only the insulting expression is labelled, and similarly only the threat 
    "action" is tagged

    Returns:
        tuple(numpy array, numpy array): data and labels

    """
    # as we have XML mixed content, we need a real XML parser...
    parser = make_parser()
    handler = TEIContentHandler()
    parser.setContentHandler(handler)
    parser.parseString(stringXml)
    tokens = handler.getSents()
    labels = handler.getAllLabels()
    return tokens, labels


def load_data_and_labels_xml_file(filepathXml):
    """
    Load data and label from an XML file
    the format is as follow:
    <p> 
        bla bla you are a <rs type="insult">CENSURED</rs>, 
        and I will <rs type="threat">find and kill</rs> you bla bla
    </p>
    only the insulting expression is labelled, and similarly only the threat 
    "action" is tagged

    Returns:
        tuple(numpy array, numpy array): data and labels

    """
    # as we have XML mixed content, we need a real XML parser...
    parser = make_parser()
    handler = TEIContentHandler()
    parser.setContentHandler(handler)
    parser.parse(filepathXml)
    tokens = handler.getSents()
    labels = handler.getAllLabels()
    return tokens, labels


def load_data_and_labels_crf_file(filepath):
    """
    Load data, features and label from a CRF matrix string 
    the format is as follow:

    token_0 f0_0 f0_1 ... f0_n label_0
    token_1 f1_0 f1_1 ... f1_n label_1
    ...
    token_m fm_0 fm_1 ... fm_n label_m

    field separator can be either space or tab

    Returns:
        tuple(numpy array, numpy array, numpy array): tokens, labels, features

    """
    sents = []
    labels = []
    featureSets = []

    with open(filepath) as f:
        tokens, tags, features = [], [], []
        for line in f:
            line = line.strip()
            if len(line) == 0:
                if len(tokens) != 0:
                    sents.append(tokens)
                    labels.append(tags)
                    featureSets.append(features)
                    tokens, tags, features = [], [], []
            else:
                #pieces = line.split('\t')
                pieces = re.split(' |\t', line)
                token = pieces[0]
                tag = pieces[len(pieces)-1]
                localFeatures = pieces[1:len(pieces)-2]
                tokens.append(token)
                tags.append(_translate_tags_grobid_to_IOB(tag))
                features.append(localFeatures)
    return np.asarray(sents), np.asarray(labels), np.asarray(featureSets)


def load_data_and_labels_crf_string(crfString):
    """
    Load data, features and label from a CRF matrix file 
    the format is as follow:

    token_0 f0_0 f0_1 ... f0_n label_0
    token_1 f1_0 f1_1 ... f1_n label_1
    ...
    token_m fm_0 fm_1 ... fm_n label_m

    field separator can be either space or tab

    Returns:
        tuple(numpy array, numpy array, numpy array): tokens, labels, features

    """
    sents = []
    labels = []
    featureSets = []

    for line in crfString.splitlines():
        tokens, tags, features = [], [], []
        line = line.strip()
        if len(line) == 0:
            if len(tokens) != 0:
                sents.append(tokens)
                labels.append(tags)
                featureSets.append(features)
                tokens, tags, features = [], [], []
        else:
            #pieces = line.split('\t')
            pieces = re.split(' |\t', line)
            token = pieces[0]
            tag = pieces[len(pieces)-1]
            localFeatures = pieces[1:len(pieces)-2]
            tokens.append(token)
            tags.append(_translate_tags_grobid_to_IOB(tag))
            features.append(localFeatures)
    return sents, labels, featureSets


def load_data_crf_string(crfString):
    """
    Load data and features from a CRF matrix file 
    the format is as follow:

    token_0 f0_0 f0_1 ... f0_n
    token_1 f1_0 f1_1 ... f1_n
    ...
    token_m fm_0 fm_1 ... fm_n

    field separator can be either space or tab

    Returns:
        tuple(numpy array, numpy array): tokens, features

    """
    sents = []
    featureSets = []



    return sents, featureSets

def _translate_tags_grobid_to_IOB(tag):
    """
    Convert labels as used by GROBID to the more standard IOB2 
    """
    if tag.endswith('other>'):
        # outside
        return 'O'
    elif tag.startswith('I-'):
        # begin
        return 'B-'+tag[2:]
    elif tag.startswith('<'):
        # inside
        return 'I-'+tag
    else:
        return tag

def load_data_and_labels_conll(filename):
    """
    Load data and label from a file.

    Args:
        filename (str): path to the file.

        The file format is tab-separated values.
        A blank line is required at the end of a sentence.

        For example:
        ```
        EU  B-ORG
        rejects O
        German  B-MISC
        call	O
        to	O
        boycott	O
        British	B-MISC
        lamb	O
        .	O

        Peter	B-PER
        Blackburn	I-PER
        ...
        ```

    Returns:
        tuple(numpy array, numpy array): data and labels

    """

    # TBD: for consistency the tokenization in the CoNLL files should not be considered, 
    # only the standard DeLFT tokenization, in line with the word embeddings
    sents, labels = [], []
    with open(filename) as f:
        words, tags = [], []
        for line in f:
            line = line.rstrip()
            if len(line) == 0 or line.startswith('-DOCSTART-'):
                if len(words) != 0:
                    sents.append(words)
                    labels.append(tags)
                    words, tags = [], []
            else:
                word, tag = line.split('\t')
                words.append(word)
                tags.append(tag)
    return np.asarray(sents), np.asarray(labels)


def load_data_and_labels_lemonde(filepathXml):
    """
    Load data and label from Le Monde XML corpus file
    the format is ENAMEX-style, as follow:
    <sentence id="E14">Les ventes de micro-ordinateurs en <ENAMEX type="Location" sub_type="Country" 
        eid="2000000003017382" name="Republic of France">France</ENAMEX> se sont ralenties en 1991. </sentence>

    Returns:
        tuple(numpy array, numpy array): data and labels

    """
    # as we have XML mixed content, we need a real XML parser...
    parser = make_parser()
    handler = ENAMEXContentHandler()
    parser.setContentHandler(handler)
    parser.parse(filepathXml)
    tokens = handler.getSents()
    labels = handler.getAllLabels()
    
    return tokens, labels


if __name__ == "__main__":
    # some tests
    xmlPath = '../../data/sequence/train.xml'
    print(xmlPath)
    sents, allLabels = load_data_and_labels_xml_file(xmlPath)
    print('toxic tokens:', sents)
    print('toxic labels:', allLabels)

    xmlPath = '../../data/sequence/test.xml'
    print(xmlPath)
    sents, allLabels = load_data_and_labels_xml_file(xmlPath)
    print('toxic tokens:', sents)
    print('toxic labels:', allLabels)

# Scikit-learn used for tf-idf
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
# And to meassure cosine similarity of sparse vectors
from sklearn.metrics.pairwise import cosine_distances

# NLTK for word tokenizing
from nltk import word_tokenize

# Scipy to stack sparse vectors
import scipy

# Gensim for Doc2Vec
from gensim.models.doc2vec import Doc2Vec, TaggedDocument

import numpy as np


class IRChatbot:

    def __init__(self, messages, edges, representation = 'tf-idf', representation_kwargs=None):
        """Calculate message representations

        Keyword arguments:
        messages -- a dictionary with (id, message), where id is a unique
         identifier and message is a string
        edges -- a list of tuples (id1, id2) where each tuple indicates that the
         message with id2 was used as a response to the message with id1
        representation -- the message representtion to be used (default: 'tf-idf')
        """

        self.messages = messages
        self.representation = representation

        # Calculate vector representations of all messages
        if self.representation == 'tf-idf':
            self.message_vectors = self.tf_idf(self.messages)
        if self.representation == 'doc2vec':
            self.message_vectors = self.doc2vec(self.messages, **representation_kwargs)

        # Convert the list of edge tuples to a dictionary (id, [id, id, id])
        self.responses = self.tuples_to_dict(edges)

    def respond(self, message):

        # Calculate message vector representation
        if self.representation == 'tf-idf':
            message_count_vector = self.tfidf_vectorizer.transform([message])
            message_vector = self.tfidf.transform(message_count_vector)[0]
        if self.representation == 'doc2vec':
            message_vector = self.doc2vec_model.infer_vector(message).reshape(1,-1)

        # Find the id of the closest message
        closest_message_id = self.find_closest_message(message_vector)

        return self.messages[self.choose_reponse_id(closest_message_id)]



    def find_closest_message(self, message_vector):

        if self.representation == 'tf-idf':
            distances = cosine_distances(message_vector,  scipy.sparse.vstack(list(self.message_vectors.values())))
        else:
            distances = cosine_distances(message_vector,  list(self.message_vectors.values()))
        best_match = list(self.message_vectors.keys())[np.argmin(distances)]

        return best_match

    def choose_reponse_id(self, id):

        # If we have no record of a reponse to the closest message, just return that message
        if id not in self.responses:
            return id
        elif len(self.responses[id]) == 1:
            return self.responses[id][0]
        else:
            # If there are multiple possible reponses, return a random None
            # TODO: Could be changed to choose the reponse with the smallest cosine distance to the message
            return self.responses[id][np.random.randint(0, len(self.responses[id]))]

    def tuples_to_dict(self, tuples):
        dictionary = {}
        for id1, id2 in tuples:
            try:
                dictionary[id1].append(id2)
            except KeyError:
                dictionary[id1] = [id2]
        return dictionary

    def tf_idf(self, documents):
        """Calculates and returns the tf-idf representation of all documents

        Keyword arguments:
        documents -- a dictionary with (id, document)

        Returns:
        Dictionary with (id, tf-idf representation)
        """

        # Count word occurences in each document
        self.tfidf_vectorizer = CountVectorizer(tokenizer=word_tokenize)
        count_vectors = self.tfidf_vectorizer.fit_transform(documents.values())

        # Convert vectors of word occurecnes to tf-idf vectors
        self.tfidf = TfidfTransformer(smooth_idf=False, norm='l2')
        tf_idf_representation = self.tfidf.fit_transform(count_vectors)

        # Map document id's to tf-idf representations
        return dict(zip(documents.keys(), tf_idf_representation))

    def doc2vec(self, documents, **kwargs):

        if 'epochs' in kwargs:
            epochs = kwargs['epochs']
        else:
            epochs = 10
        if 'vector_size' in kwargs:
            vector_size = kwargs['vector_size']
        else:
            vector_size = 20

        # Tag the documents to all have their own class
        tagged_documents = [TaggedDocument(doc, [i]) for i, doc in enumerate(documents.values())]

        # Initiate and train doc2vec model
        self.doc2vec_model = Doc2Vec(vector_size=vector_size, window=2, min_count=1, seed=0, epochs=epochs)
        self.doc2vec_model.build_vocab(tagged_documents)
        self.doc2vec_model.train(tagged_documents, total_examples=self.doc2vec_model.corpus_count, epochs=self.doc2vec_model.epochs)

        self.doc2vec_model.delete_temporary_training_data(keep_doctags_vectors=True, keep_inference=True)

        doc2vec_representation = [self.doc2vec_model.infer_vector(message) for message in documents.values()]

        return dict(zip(documents.keys(), doc2vec_representation))

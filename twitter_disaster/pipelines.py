# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


from itemadapter import ItemAdapter
import os
import spacy
from elasticsearch import Elasticsearch
from datasets import Dataset
from transformers import BertTokenizer, BertForSequenceClassification, Trainer


class TwitterDisasterPipeline:
    def process_item(self, item, spider):
        return item


class TweetProcessingPipeline:
    def open_spider(self, spider):

        # BERT Model
        self.model = BertForSequenceClassification.from_pretrained('./twitter_disaster/disaster_tweet_model')  # Path to the saved model
        self.tokenizer = BertTokenizer.from_pretrained('./twitter_disaster/disaster_tweet_model')  # Path to the saved tokenizer
        self.trainer = Trainer(model=self.model)

        # Spacy
        self.nlp = spacy.load("en_core_web_lg")

        # Elastic Search
        self.es = Elasticsearch(
            hosts=[os.environ['ELASTIC_URL']],
        )
        self.index_name = "unverified_posts"

        # Disaster Types
        self.natural_disasters = {
            'earthquake': ['earthquake', 'shake', 'seismic', 'tremor'],
            'flood': ['flood', 'water', 'rain', 'submerge', 'deluge'],
            'storm': ['storm', 'thunderstorm', 'hurricane', 'tornado', 'twister'],
            'fire': ['fire', 'wildfire', 'blaze', 'flames'],
            'human_disaster': ['explosion', 'crash', 'accident', 'shooting', 'violence', 'bomb', 'building collapse'],
        }

    def process_item(self, item, spider):

        text_encodings = self.tokenizer([item['post_body']], padding=True, truncation=True, max_length=128)
        text_dataset = Dataset.from_dict({
            'input_ids': text_encodings['input_ids'],
            'attention_mask': text_encodings['attention_mask']
        })

        predictions = self.trainer.predict(text_dataset)
        predicted_labels = predictions.predictions.argmax(-1)
        if (predicted_labels[0] != 1):
            return item

        def extract_locations_and_incidents(tweet):
            doc = self.nlp(tweet)
            locations = []
            incident_type = None

            # Extract locations
            for entity in doc.ents:
                if entity.label_ in ['GPE', 'LOC']:  # GPE (Geopolitical Entity), LOC (Location)
                    locations.append(entity.text)

            # Check for natural disaster-related contexts
            for disaster, keywords in self.natural_disasters.items():
                if any(keyword in tweet.lower() for keyword in keywords):
                    incident_type = disaster.capitalize()
                    break

            # If no category found, mark as unknown
            if not incident_type:
                incident_type = None

            return locations, incident_type
            
        locations, disaster_type = extract_locations_and_incidents(item['post_body'])

        if locations:
            item['location'] = item.get('location', "") + ", ".join(locations)
        if disaster_type:
            item['disaster_type'] = disaster_type
        item['source'] = "Twitter"

        # Index the processed item into Elasticsearch
        self.es.index(index=self.index_name, document=dict(item))
    #     # spider.logger.info(f"Tweet {item['tweet_id']} processed and indexed into Elasticsearch.")
        return item

    def close_spider(self, spider):
        self.es.close()
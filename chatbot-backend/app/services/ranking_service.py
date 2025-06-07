from google.cloud.discoveryengine_v1 import RankServiceClient, RankRequest, RankingRecord
from flask import current_app

class RankingService:
    def __init__(self):
        self.client = RankServiceClient()

    def rank_documents(self, query, documents, top_n=10):
        """
        Reranks a list of documents based on a query using the Discovery Engine Ranking API.

        :param query: The user's query string.
        :param documents: A list of dictionaries, where each dictionary represents a document
                          with 'id', 'title', and 'content' keys.
        :param top_n: The number of top-ranked documents to return.
        :return: A list of reranked documents.
        """
        project_id = current_app.config.get("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            current_app.logger.error("GOOGLE_CLOUD_PROJECT not set in config.")
            return documents # Return original documents if project_id is not set

        ranking_config = self.client.ranking_config_path(
            project=project_id,
            location="global",
            ranking_config="default_ranking_config",
        )

        records = [
            RankingRecord(
                id=str(doc.get('id', '')),
                title=doc.get('metadata', {}).get('title', ''),
                content=doc.get('page_content', '')
            )
            for doc in documents
        ]

        request = RankRequest(
            ranking_config=ranking_config,
            model="semantic-ranker-default-004",
            top_n=top_n,
            query=query,
            records=records,
        )

        try:
            response = self.client.rank(request=request)
            
            ranked_docs_map = {record.id: record.score for record in response.records}
            
            # Create a new list of documents in the ranked order
            reranked_documents = sorted(documents, key=lambda doc: ranked_docs_map.get(str(doc.get('id')), -1), reverse=True)
            
            return reranked_documents

        except Exception as e:
            current_app.logger.error(f"Error ranking documents: {e}")
            # Fallback to returning the original documents if ranking fails
            return documents

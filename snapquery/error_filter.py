"""
Created on 2024-05-06

@author: wf
"""


class ErrorFilter:
    """
    handle technical error message to
    retrieve user friendly content
    """

    def __init__(self, raw_error_message: str):
        self.raw_error_message = raw_error_message
        self.filtered_message = self._extract_relevant_info()

    def _extract_relevant_info(self) -> str:
        # Extract SPARQL query if present
        sparql_start_token = "SPARQL-QUERY:"
        sparql_end_token = "java.util.concurrent.ExecutionException"

        # Extract the malformed query
        sparql_start_idx = self.raw_error_message.find(sparql_start_token)
        sparql_end_idx = self.raw_error_message.find(sparql_end_token)

        if sparql_start_idx != -1 and sparql_end_idx != -1:
            sparql_query = self.raw_error_message[sparql_start_idx:sparql_end_idx]
            sparql_query = sparql_query.replace("SPARQL-QUERY:", "").strip()
        else:
            sparql_query = "SPARQL query not found."

        # Find and include error message
        error_summary = "Query error: A bad request was sent to the endpoint, possibly due to a malformed SPARQL query."

        # Combine error message and SPARQL query
        filtered_message = f"{error_summary}\n\nMalformed Query:\n{sparql_query}"

        return filtered_message

    def get_message(self, for_html: bool = True) -> str:
        """
        get the filtered message
        """
        filtered_msg = self.filtered_message
        if for_html:
            filtered_msg = filtered_msg.replace("\n", "<br>\n")
            filtered_msg = filtered_msg.replace("\\n", "<br>\n")
        return filtered_msg

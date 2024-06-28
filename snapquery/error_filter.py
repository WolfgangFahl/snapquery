"""
Created on 2024-05-06

@author: wf
"""
from typing import Union


class ErrorFilter:
    """
    handle technical error message to
    retrieve user friendly content
    """

    def __init__(self, raw_error_message: str):
        self.raw_error_message = raw_error_message
        self.filtered_message = self._extract_relevant_info()
        self.category = self.categorize_error()

    def categorize_error(self) -> str:
        """
        Categorizes the error message into predefined types.

        Returns:
            str: The category of the error message.
        """
        if self.raw_error_message is None:
            return None

        lower_error_msg = self.raw_error_message.lower()
        # Todo: query is often part of the error message when these keywords are used within the query the classification fails.
        if (
                "timeout" in lower_error_msg
                or "query has timed out" in lower_error_msg
                or "http error 504" in lower_error_msg
        ):
            return "Timeout"
        elif (
            "syntax error" in lower_error_msg
            or "invalid sparql query" in lower_error_msg
            or "querybadformed" in lower_error_msg
        ):
            return "Syntax Error"
        elif "connection error" in lower_error_msg:
            return "Connection Error"
        elif "access denied" in lower_error_msg:
            return "Authorization Error"
        elif (
                "service unavailable" in lower_error_msg
                or "service temporarily unavailable" in lower_error_msg
                or "http error 503" in lower_error_msg
        ):
            return "Service Unavailable"
        elif (
                "too many requests" in lower_error_msg
                or "http error 429" in lower_error_msg
        ):
            return "Too Many Requests"
        elif (
                "bad gateway" in lower_error_msg
                or "http error 502" in lower_error_msg
        ):
            return "Bad Gateway"
        elif "endpointinternalerror" in lower_error_msg:
            return "EndPointInternalError"
        else:
            return "Other"

    def _extract_relevant_info(self) -> str:
        """
        Extract relevant information from the given raw error message.
        Identifies and processes different error message formats.
        """
        if not self.raw_error_message:
            return None

        if "SPARQL-QUERY:" in self.raw_error_message:
            return self._extract_sparql_error()
        elif "Not supported:" in self.raw_error_message:
            return self._extract_qlever_error()
        elif "Invalid SPARQL query" in self.raw_error_message:
            return self._extract_invalid_sparql_error()
        elif self.raw_error_message.startswith("QueryBadFormed:") and "Virtuoso" in self.raw_error_message:
            return self._extract_virtuoso_error()
        else:
            return "Error: Unrecognized error format."

    def _extract_sparql_error(self) -> str:
        """
        Specifically extract and format SPARQL error messages.
        """
        sparql_start_token = "SPARQL-QUERY:"
        sparql_end_token = "java.util.concurrent.ExecutionException"
        sparql_query = self._extract_message_between_tokens(sparql_start_token, sparql_end_token)
        if sparql_query:
            return f"Query error in SPARQL:\n{sparql_query}"
        else:
            return "Error: SPARQL query information is incomplete."

    def _extract_qlever_error(self) -> str:
        """
        Specifically extract and format QLever error messages.
        """
        start_idx = self.raw_error_message.find("Not supported:")
        if start_idx != -1:
            end_idx = self.raw_error_message.find("}", start_idx)
            error_message = self.raw_error_message[start_idx : end_idx + 1].strip()
            return f"QLever error:\n{error_message}"
        else:
            return "Error: QLever error information is incomplete."

    def _extract_virtuoso_error(self) -> str:
        """
        Specifically extract and format virtuoso error messages.
        Returns:

        """
        start_token = "Response: b'"
        end_token = "SPARQL query:"
        message = self._extract_message_between_tokens(start_token, end_token)
        if message:
            return f"Virtuoso error:\n{message}"
        else:
            return "Error: Virtuoso error information is incomplete."

    def _extract_message_between_tokens(self, start_token: str, end_token: str) -> Union[str, None]:
        """
        Extract and format message between tokens.
        Args:
            start_token:
            end_token:

        Returns:

        """
        start_idx = self.raw_error_message.find(start_token)
        end_idx = self.raw_error_message.find(end_token)
        message = None
        if start_idx != -1 and end_idx != -1:
            message = self.raw_error_message[start_idx:end_idx]
            message = message[len(start_token):]
            message = message.strip()
        return message


    def _extract_invalid_sparql_error(self) -> str:
        """
        Specifically extract and format Invalid SPARQL query error messages.
        """
        error_start = self.raw_error_message.find("Invalid SPARQL query")
        if error_start != -1:
            error_msg = self.raw_error_message[error_start:].split("\n")[0]
            return f"Invalid SPARQL query error:\n{error_msg}"
        else:
            return "Error: Invalid SPARQL query information is incomplete."

    def get_message(self, for_html: bool = True) -> str:
        """
        get the filtered message
        """
        filtered_msg = self.filtered_message
        if filtered_msg:
            filtered_msg = filtered_msg.replace("\\n", "\n")
            if for_html:
                filtered_msg = filtered_msg.replace("\n", "<br>\n")
        return filtered_msg

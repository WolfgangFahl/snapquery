"""
Created on 2024-05-06

@author: wf
"""
import json
from json import JSONDecodeError
from typing import Union


class ErrorFilter:
    """
    handle technical error message to
    retrieve user friendly content
    """

    def __init__(self, raw_error_message: str):
        self.raw_error_message = raw_error_message
        self.category = self.categorize_error()
        self.filtered_message = self._extract_relevant_info()

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
            "query timeout after" in lower_error_msg
            or "timeoutexception" in lower_error_msg
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
        elif "bad gateway" in lower_error_msg or "http error 502" in lower_error_msg:
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
        elif (
            self.raw_error_message.startswith("QueryBadFormed:")
            and "Virtuoso" in self.raw_error_message
        ):
            return self._extract_virtuoso_error()
        elif self.raw_error_message.startswith("QueryBadFormed:"):
            return self._extract_triply_db_error()
        elif "Not supported:" in self.raw_error_message:
            return self._extract_qlever_error()
        elif "Invalid SPARQL query" in self.raw_error_message:
            return self._extract_invalid_sparql_error()
        else:
            if self.category == "Timeout":
                return "Query has timed out."
            message_json = self._get_error_message_json()
            if (
                message_json
                and isinstance(message_json, dict)
                and "exception" in message_json
            ):
                return message_json.get("exception")
            return "Error: Unrecognized error format."

    def _extract_sparql_error(self) -> str:
        """
        Specifically extract and format SPARQL error messages.
        """
        if "java.util.concurrent.TimeoutException" in self.raw_error_message:
            return "Query has timed out."
        sparql_start_token = "SPARQL-QUERY:"
        sparql_end_token = "java.util.concurrent.ExecutionException"
        sparql_query = self._extract_message_between_tokens(
            sparql_start_token, sparql_end_token
        )
        error_log_start = sparql_end_token
        error_log_start_idx = self.raw_error_message.find(error_log_start)
        error_log_end_idx = self.raw_error_message.find("\\tat", error_log_start_idx)
        error_message = self.raw_error_message[error_log_start_idx:error_log_end_idx]
        if error_message:
            return (
                error_message.split("Exception:")[-1]
                .encode("utf-8")
                .decode("unicode_escape")
                .strip()
            )
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
            return message
        else:
            return "Error: Virtuoso error information is incomplete."

    def _extract_triply_db_error(self) -> str:
        """
        Specifically extract and format TriplyDB error messages.
        Returns:

        """
        message_json = self._get_error_message_json()
        if message_json and "message" in message_json:
            return message_json.get("message")
        elif message_json and "exception" in message_json:
            return message_json.get("exception")
        else:
            return "Error: TriplyDB error information is incomplete."

    def _get_error_message_json(self) -> Union[dict, None]:
        """
        Try to extract the json record from the raw error message.
        """
        start_token = "Response:\nb'"
        stat_idx = self.raw_error_message.find(start_token)
        end_idx = -1
        message_json_raw = self.raw_error_message[
            stat_idx + len(start_token) : end_idx
        ].strip()
        try:
            message_json = json.loads(
                message_json_raw.encode().decode("unicode_escape")
            )
        except JSONDecodeError as e:
            message_json = None
        return message_json

    def _extract_message_between_tokens(
        self, start_token: str, end_token: str
    ) -> Union[str, None]:
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
            message = message[len(start_token) :]
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

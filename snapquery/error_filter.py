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

        if "timeout" in lower_error_msg:
            return "Timeout"
        elif (
            "syntax error" in lower_error_msg
            or "invalid sparql query" in lower_error_msg
        ):
            return "Syntax Error"
        elif "connection error" in lower_error_msg:
            return "Connection Error"
        elif "access denied" in lower_error_msg:
            return "Authorization Error"
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
        else:
            return "Error: Unrecognized error format."

    def _extract_sparql_error(self) -> str:
        """
        Specifically extract and format SPARQL error messages.
        """
        sparql_start_token = "SPARQL-QUERY:"
        sparql_end_token = "java.util.concurrent.ExecutionException"
        sparql_start_idx = self.raw_error_message.find(sparql_start_token)
        sparql_end_idx = self.raw_error_message.find(sparql_end_token)

        if sparql_start_idx != -1 and sparql_end_idx != -1:
            sparql_query = self.raw_error_message[sparql_start_idx:sparql_end_idx]
            sparql_query = sparql_query.replace("SPARQL-QUERY:", "").strip()
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

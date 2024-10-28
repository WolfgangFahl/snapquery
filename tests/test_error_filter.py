"""
Created on 2024-05-06

@author: wf
"""

import unittest
from pathlib import Path

from dacite import from_dict
from ngwidgets.basetest import Basetest

from snapquery.error_filter import ErrorFilter
from snapquery.snapquery_core import NamedQueryManager, QueryStats, QueryStatsList


class TestErrorFilter(Basetest):
    """
    test the error filter according to
    https://github.com/WolfgangFahl/snapquery/issues/20
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.nqm = NamedQueryManager()
        self.example_errs = [
            (
                """QueryBadFormed: A bad request has been sent to the endpoint: probably the SPARQL query is badly formed. Response: b'SPARQL-QUERY: queryStr=#\n#title: Variants of author name strings\nPREFIX target: \n\nSELECT \n (COUNT(?work) AS ?count)\n ?string\n (CONCAT("https://author-disambiguator.toolforge.org/names_oauth.php?doit=Look+for+author&name=", \n ENCODE_FOR_URI(?string)) AS ?author_resolver_url) \nWITH\n{\n # Find strings associated with the target author\n SELECT DISTINCT ?string_\n WHERE\n {\n { target: rdfs:label ?string_. } # in label\n UNION\n { target: skos:altLabel ?string_. } # in alias\n UNION\n {\n ?author_statement ps:P50 target: ; \n pq:P1932 ?string_. # in "stated as" strings for "author" statements on work items\n }\n }\n} AS %RAWstrings\nWITH\n# This part is due to Dipsacus fullonum, as per https://w.wiki/5Brk\n{\n # Calculate capitalization variants of these raw strings\n SELECT DISTINCT ?string\n WHERE\n {\n {\n INCLUDE %RAWstrings\n BIND(STR(?string_) AS ?string) # the raw strings\n }\n UNION\n {\n INCLUDE %RAWstrings\n BIND(UCASE(STR(?string_)) AS ?string) # uppercased versions of the raw strings\n }\n UNION\n {\n INCLUDE %RAWstrings\n BIND(LCASE(STR(?string_)) AS ?string) # lowercased versions of the raw strings\n }\n }\n} AS %NORMALIZEDstrings\nWHERE {\n # Find works that have "author name string" values equal to these normalized strings\n INCLUDE %NORMALIZEDstrings\n OPTIONAL { ?work wdt:P2093 ?string. }\n}\nGROUP BY ?string\nORDER BY DESC (?count)\n\nLIMIT 200\njava.util.concurrent.ExecutionException: org.openrdf.query.MalformedQueryException: Encountered " "<" "< "" at line 3, column 16.\nWas expecting:\n ...\n \n\\tat java.util.concurrent.FutureTask.report(FutureTask.java:122)\n\tat java.util.concurrent.FutureTask.get(FutureTask.java:206)\n\tat com.bigdata.rdf.sail.webapp.BigdataServlet.submitApiTask(BigdataServlet.java:292)\n\tat com.bigdata.rdf.sail.webapp.QueryServlet.doSparqlQuery(QueryServlet.java:678)\n\tat com.bigdata.rdf.sail.webapp.QueryServlet.doPost(QueryServlet.java:275)\n\tat com.bigdata.rdf.sail.webapp.RESTServlet.doPost(RESTServlet.java:269)\n\tat com.bigdata.rdf.sail.webapp.MultiTenancyServlet.doPost(MultiTenancyServlet.java:195)\n\tat javax.servlet.http.HttpServlet.service(HttpServlet.java:707)\n\tat javax.servlet.http.HttpServlet.service(HttpServlet.java:790)\n\tat org.eclipse.jetty.servlet.ServletHolder.handle(ServletHolder.java:865)\n\tat org.eclipse.jetty.servlet.ServletHandler$CachedChain.doFilter(ServletHandler.java:1655)\n\tat org.wikidata.query.rdf.blazegraph.throttling.ThrottlingFilter.doFilter(ThrottlingFilter.java:320)\n\tat org.eclipse.jetty.servlet.ServletHandler$CachedChain.doFilter(ServletHandler.java:1642)\n\tat org.wikidata.query.rdf.blazegraph.throttling.SystemOverloadFilter.doFilter(SystemOverloadFilter.java:82)\n\tat org.eclipse.jetty.servlet.ServletHandler$CachedChain.doFilter(ServletHandler.java:1642)\n\tat ch.qos.logback.classic.helpers.MDCInsertingServletFilter.doFilter(MDCInsertingServletFilter.java:50)\n\tat org.eclipse.jetty.servlet.ServletHandler$CachedChain.doFilter(ServletHandler.java:1642)\n\tat org.wikidata.query.rdf.blazegraph.filters.QueryEventSenderFilter.doFilter(QueryEventSenderFilter.java:122)\n\tat org.eclipse.jetty.servlet.ServletHandler$CachedChain.doFilter(ServletHandler.java:1642)\n\tat org.wikidata.query.rdf.blazegraph.filters.ClientIPFilter.doFilter(ClientIPFilter.java:43)\n\tat org.eclipse.jetty.servlet.ServletHandler$CachedChain.doFilter(ServletHandler.java:1642)\n\tat org.wikidata.query.rdf.blazegraph.filters.JWTIdentityFilter.doFilter(JWTIdentityFilter.java:66)\n\tat org.eclipse.jetty.servlet.ServletHandler$CachedChain.doFilter(ServletHandler.java:1642)\n\tat org.wikidata.query.rdf.blazegraph.filters.RealAgentFilter.doFilter(RealAgentFilter.java:33)\n\tat org.eclipse.jetty.servlet.ServletHandler$CachedChain.doFilter(ServletHandler.java:1642)\n\tat org.wikidata.query.rdf.blazegraph.filters.RequestConcurrencyFilter.doFilter(RequestConcurrencyFilter.java:50)\n\tat org.eclipse.jetty.servlet.ServletHandler$CachedChain.doFilter(ServletHandler.java:1634)\n\tat org.eclipse.jetty.servlet.ServletHandler.doHandle(ServletHandler.java:533)\n\tat org.eclipse.jetty.server.handler.ScopedHandler.handle(ScopedHandler.java:146)\n\tat org.eclipse.jetty.security.SecurityHandler.handle(SecurityHandler.java:548)\n\tat org.eclipse.jetty.server.handler.HandlerWrapper.handle(HandlerWrapper.java:132)\n\tat org.eclipse.jetty.server.handler.ScopedHandler.nextHandle(ScopedHandler.java:257)\n\tat org.eclipse.jetty.server.session.SessionHandler.doHandle(SessionHandler.java:1595)\n\tat org.eclipse.jetty.server.handler.ScopedHandler.nextHandle(ScopedHandler.java:255)\n\tat org.eclipse.jetty.server.handler.ContextHandler.doHandle(ContextHandler.java:1340)\n\tat org.eclipse.jetty.server.handler.ScopedHandler.nextScope(ScopedHandler.java:203)\n\tat org.eclipse.jetty.servlet.ServletHandler.doScope(ServletHandler.java:473)\n\tat org.eclipse.jetty.server.session.SessionHandler.doScope(SessionHandler.java:1564)\n\tat org.eclipse.jetty.server.handler.ScopedHandler.nextScope(ScopedHandler.java:201)\n\tat org.eclipse.jetty.server.handler.ContextHandler.doScope(ContextHandler.java:1242)\n\tat org.eclipse.jetty.server.handler.ScopedHandler.handle(ScopedHandler.java:144)\n\tat org.eclipse.jetty.server.handler.ContextHandlerCollection.handle(ContextHandlerCollection.java:220)\n\tat org.eclipse.jetty.server.handler.HandlerCollection.handle(HandlerCollection.java:126)\n\tat org.eclipse.jetty.server.handler.HandlerWrapper.handle(HandlerWrapper.java:132)\n\tat org.eclipse.jetty.server.Server.handle(Server.java:503)\n\tat org.eclipse.jetty.server.HttpChannel.handle(HttpChannel.java:364)\n\tat org.eclipse.jetty.server.HttpConnection.onFillable(HttpConnection.java:260)\n\tat org.eclipse.jetty.io.AbstractConnection$ReadCallback.succeeded(AbstractConnection.java:305)\n\tat org.eclipse.jetty.io.FillInterest.fillable(FillInterest.java:103)\n\tat org.eclipse.jetty.io.ChannelEndPoint$2.run(ChannelEndPoint.java:118)\n\tat org.eclipse.jetty.util.thread.strategy.EatWhatYouKill.runTask(EatWhatYouKill.java:333)\n\tat org.eclipse.jetty.util.thread.strategy.EatWhatYouKill.doProduce(EatWhatYouKill.java:310)\n\tat org.eclipse.jetty.util.thread.strategy.EatWhatYouKill.tryProduce(EatWhatYouKill.java:168)\n\tat org.eclipse.jetty.util.thread.strategy.EatWhatYouKill.run(EatWhatYouKill.java:126)\n\tat org.eclipse.jetty.util.thread.ReservedThreadExecutor$ReservedThread.run(ReservedThreadExecutor.java:366)\n\tat org.eclipse.jetty.util.thread.QueuedThreadPool.runJob(QueuedThreadPool.java:765)\n\tat org.eclipse.jetty.util.thread.QueuedThreadPool$2.run(QueuedThreadPool.java:683)\n\tat java.lang.Thread.run(Thread.java:750)\nCaused by: org.openrdf.query.MalformedQueryException: Encountered " "<" "< "" at line 3, column 16.\nWas expecting:\n ...\n \n\tat com.bigdata.rdf.sail.sparql.Bigdata2ASTSPARQLParser.parseQuery2(Bigdata2ASTSPARQLParser.java:400)\n\tat com.bigdata.rdf.sail.webapp.QueryServlet$SparqlQueryTask.call(QueryServlet.java:741)\n\tat com.bigdata.rdf.sail.webapp.QueryServlet$SparqlQueryTask.call(QueryServlet.java:695)\n\tat com.bigdata.rdf.task.ApiTaskForIndexManager.call(ApiTaskForIndexManager.java:68)\n\tat java.util.concurrent.FutureTask.run(FutureTask.java:266)\n\tat java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)\n\tat java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)\n\t... 1 more\nCaused by: com.bigdata.rdf.sail.sparql.ast.ParseException: Encountered " "<" "< "" at line 3, column 16.\nWas expecting:\n ...\n \n\tat com.bigdata.rdf.sail.sparql.ast.SyntaxTreeBuilder.generateParseException(SyntaxTreeBuilder.java:9722)\n\tat com.bigdata.rdf.sail.sparql.ast.SyntaxTreeBuilder.jj_consume_token(SyntaxTreeBuilder.java:9589)\n\tat com.bigdata.rdf.sail.sparql.ast.SyntaxTreeBuilder.IRI(SyntaxTreeBuilder.java:7527)\n\tat com.bigdata.rdf.sail.sparql.ast.SyntaxTreeBuilder.PrefixDecl(SyntaxTreeBuilder.java:296)\n\tat com.bigdata.rdf.sail.sparql.ast.SyntaxTreeBuilder.Prolog(SyntaxTreeBuilder.java:257)\n\tat com.bigdata.rdf.sail.sparql.ast.SyntaxTreeBuilder.QueryContainer(SyntaxTreeBuilder.java:215)\n\tat com.bigdata.rdf.sail.sparql.ast.SyntaxTreeBuilder.parseQuery(SyntaxTreeBuilder.java:32)\n\tat com.bigdata.rdf.sail.sparql.Bigdata2ASTSPARQLParser.parseQuery2(Bigdata2ASTSPARQLParser.java:336)\n\t... 7 more\n'""",
                "com.bigdata",
                "Encountered",
            ),
            (
                """b'{\n    "exception": "Not supported: Function \\"<http://www.w3.org/2001/XMLSchema#date>\\" is currently not supported by QLever.",\n    "metadata": {\n        "line": 37,\n        "positionInLine": 3,\n        "query": "#\\nPREFIX bd: <http://www.bigdata.com/rdf#>\\nPREFIX cc: <http://creativecommons.org/ns#>\\nPREFIX dct: <http://purl.org/dc/terms/>\\nPREFIX geo: <http://www.opengis.net/ont/geosparql#>\\nPREFIX ontolex: <http://www.w3.org/ns/lemon/ontolex#>\\nPREFIX owl: <http://www.w3.org/2002/07/owl#>\\nPREFIX p: <http://www.wikidata.org/prop/>\\nPREFIX pq: <http://www.wikidata.org/prop/qualifier/>\\nPREFIX pqn: <http://www.wikidata.org/prop/qualifier/value-normalized/>\\nPREFIX pqv: <http://www.wikidata.org/prop/qualifier/value/>\\nPREFIX pr: <http://www.wikidata.org/prop/reference/>\\nPREFIX prn: <http://www.wikidata.org/prop/reference/value-normalized/>\\nPREFIX prov: <http://www.w3.org/ns/prov#>\\nPREFIX prv: <http://www.wikidata.org/prop/reference/value/>\\nPREFIX ps: <http://www.wikidata.org/prop/statement/>\\nPREFIX psn: <http://www.wikidata.org/prop/statement/value-normalized/>\\nPREFIX psv: <http://www.wikidata.org/prop/statement/value/>\\nPREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\\nPREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\\nPREFIX schema: <http://schema.org/>\\nPREFIX skos: <http://www.w3.org/2004/02/skos/core#>\\nPREFIX wd: <http://www.wikidata.org/entity/>\\nPREFIX wdata: <http://www.wikidata.org/wiki/Special:EntityData/>\\nPREFIX wdno: <http://www.wikidata.org/prop/novalue/>\\nPREFIX wdref: <http://www.wikidata.org/reference/>\\nPREFIX wds: <http://www.wikidata.org/entity/statement/>\\nPREFIX wdt: <http://www.wikidata.org/prop/direct/>\\nPREFIX wdtn: <http://www.wikidata.org/prop/direct-normalized/>\\nPREFIX wdv: <http://www.wikidata.org/value/>\\nPREFIX wikibase: <http://wikiba.se/ontology#>\\nPREFIX xsd: <http://www.w3.org/2001/XMLSchema#>\\n\\nPREFIX target: <http://www.wikidata.org/entity/Q80>\\n\\nSELECT\\n  (xsd:date(MIN(?start)) AS ?date)  \\n  ?event ?eventLabel\\n  (CONCAT(\\"/event/\\", SUBSTR(STR(?event), 32)) AS ?eventUrl)\\n  (GROUP_CONCAT(DISTINCT ?role; separator=\\", \\") AS ?roles)\\n  (GROUP_CONCAT(DISTINCT ?location_label; separator=\\", \\") AS ?locations)\\nWHERE {\\n    BIND(target: AS ?person)\\n    {  # speaker\\n      ?event wdt:P823 ?person .\\n      BIND(\\"speaker\\" AS ?role)\\n    } UNION {  # organizer\\n      ?event wdt:P664 ?person .\\n      BIND(\\"organizer\\" AS ?role)\\n    } UNION {  # participant\\n      ?person wdt:P1344 | ^wdt:P710 ?event  .\\n      BIND(\\"participant\\" AS ?role)\\n    } UNION {  # editor\\n      ?person ^wdt:P98 / wdt:P4745 ?event  .\\n      BIND(\\"editor of proceedings\\" AS ?role)\\n    } UNION {  # author\\n      ?person ^wdt:P50 / wdt:P1433 / wdt:P4745 ?event  .\\n      BIND(\\"author\\" AS ?role)\\n    } UNION {  # program committee member\\n      ?event wdt:P5804 ?person .\\n      BIND(\\"program committee member\\" AS ?role)\\n    }\\n    OPTIONAL { ?event wdt:P276 ?location . ?location rdfs:label ?location_label . FILTER (LANG(?location_label) = \'en\')}\\n    OPTIONAL { ?event wdt:P580 | wdt:P585 ?start }\\n \\n    SERVICE wikibase:label { bd:serviceParam wikibase:language \\"[AUTO_LANGUAGE],en,da,de,es,fr,jp,no,ru,sv,zh\\". }\\n}\\nGROUP BY ?event ?eventLabel\\nORDER BY DESC(?date) \\n",\n        "startIndex": 1700,\n        "stopIndex": 1720\n    },\n    "query": "#\\nPREFIX bd: <http://www.bigdata.com/rdf#>\\nPREFIX cc: <http://creativecommons.org/ns#>\\nPREFIX dct: <http://purl.org/dc/terms/>\\nPREFIX geo: <http://www.opengis.net/ont/geosparql#>\\nPREFIX ontolex: <http://www.w3.org/ns/lemon/ontolex#>\\nPREFIX owl: <http://www.w3.org/2002/07/owl#>\\nPREFIX p: <http://www.wikidata.org/prop/>\\nPREFIX pq: <http://www.wikidata.org/prop/qualifier/>\\nPREFIX pqn: <http://www.wikidata.org/prop/qualifier/value-normalized/>\\nPREFIX pqv: <http://www.wikidata.org/prop/qualifier/value/>\\nPREFIX pr: <http://www.wikidata.org/prop/reference/>\\nPREFIX prn: <http://www.wikidata.org/prop/reference/value-normalized/>\\nPREFIX prov: <http://www.w3.org/ns/prov#>\\nPREFIX prv: <http://www.wikidata.org/prop/reference/value/>\\nPREFIX ps: <http://www.wikidata.org/prop/statement/>\\nPREFIX psn: <http://www.wikidata.org/prop/statement/value-normalized/>\\nPREFIX psv: <http://www.wikidata.org/prop/statement/value/>\\nPREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\\nPREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\\nPREFIX schema: <http://schema.org/>\\nPREFIX skos: <http://www.w3.org/2004/02/skos/core#>\\nPREFIX wd: <http://www.wikidata.org/entity/>\\nPREFIX wdata: <http://www.wikidata.org/wiki/Special:EntityData/>\\nPREFIX wdno: <http://www.wikidata.org/prop/novalue/>\\nPREFIX wdref: <http://www.wikidata.org/reference/>\\nPREFIX wds: <http://www.wikidata.org/entity/statement/>\\nPREFIX wdt: <http://www.wikidata.org/prop/direct/>\\nPREFIX wdtn: <http://www.wikidata.org/prop/direct-normalized/>\\nPREFIX wdv: <http://www.wikidata.org/value/>\\nPREFIX wikibase: <http://wikiba.se/ontology#>\\nPREFIX xsd: <http://www.w3.org/2001/XMLSchema#>\\n\\nPREFIX target: <http://www.wikidata.org/entity/Q80>\\n\\nSELECT\\n  (xsd:date(MIN(?start)) AS ?date)  \\n  ?event ?eventLabel\\n  (CONCAT(\\"/event/\\", SUBSTR(STR(?event), 32)) AS ?eventUrl)\\n  (GROUP_CONCAT(DISTINCT ?role; separator=\\", \\") AS ?roles)\\n  (GROUP_CONCAT(DISTINCT ?location_label; separator=\\", \\") AS ?locations)\\nWHERE {\\n    BIND(target: AS ?person)\\n    {  # speaker\\n      ?event wdt:P823 ?person .\\n      BIND(\\"speaker\\" AS ?role)\\n    } UNION {  # organizer\\n      ?event wdt:P664 ?person .\\n      BIND(\\"organizer\\" AS ?role)\\n    } UNION {  # participant\\n      ?person wdt:P1344 | ^wdt:P710 ?event  .\\n      BIND(\\"participant\\" AS ?role)\\n    } UNION {  # editor\\n      ?person ^wdt:P98 / wdt:P4745 ?event  .\\n      BIND(\\"editor of proceedings\\" AS ?role)\\n    } UNION {  # author\\n      ?person ^wdt:P50 / wdt:P1433 / wdt:P4745 ?event  .\\n      BIND(\\"author\\" AS ?role)\\n    } UNION {  # program committee member\\n      ?event wdt:P5804 ?person .\\n      BIND(\\"program committee member\\" AS ?role)\\n    }\\n    OPTIONAL { ?event wdt:P276 ?location . ?location rdfs:label ?location_label . FILTER (LANG(?location_label) = \'en\')}\\n    OPTIONAL { ?event wdt:P580 | wdt:P585 ?start }\\n \\n    SERVICE wikibase:label { bd:serviceParam wikibase:language \\"[AUTO_LANGUAGE],en,da,de,es,fr,jp,no,ru,sv,zh\\". }\\n}\\nGROUP BY ?event ?eventLabel\\nORDER BY DESC(?date) \\n",\n    "resultsize": 0,\n    "status": "ERROR",\n    "time": {\n        "computeResult": 2,\n        "total": 2\n    }\n}'""",
                "exception",
                "XMLSchema#date",
            ),
        ]

    def test_error_categories(self):
        """
        Test the error categorization functionality of ErrorFilter
        """
        test_cases = [
            ("Query timeout after 60 seconds", "Timeout"),
            ("Syntax error in SPARQL query", "Syntax Error"),
            ("Invalid SPARQL query: Unexpected token", "Syntax Error"),
            ("Connection error: Unable to reach endpoint", "Connection Error"),
            ("Access denied: Insufficient permissions", "Authorization Error"),
            ("Unknown error occurred", "Other"),
            ("HTTP Error 503: Service Unavailable", "Service Unavailable"),
            ("HTTP Error 502: Bad Gateway ", "Bad Gateway"),
            ("HTTP Error 502", "Bad Gateway"),
            ("HTTP Error 504: Query has timed out.", "Timeout"),
            ("HTTP Error 504", "Timeout"),
            (
                "QueryBadFormed: A bad request has been sent to the endpoint: probably the SPARQL query is badly formed. Response: [...] ",
                "Syntax Error",
            ),
            ("HTTP Error 503: Service Temporarily Unavailable.", "Service Unavailable"),
            ("HTTP Error 503", "Service Unavailable"),
            ("HTTP Error 429: Too Many Requests", "Too Many Requests"),
            ("HTTP Error 429", "Too Many Requests"),
            (
                "EndPointInternalError: The endpoint returned the HTTP status code 500. Response: b'Virtuoso 42000 Error SQ070:SECURITY [...]",
                "EndPointInternalError",
            ),
            (
                "QueryBadFormed: A bad request has been sent to the endpoint: probably the SPARQL query is badly formed. Response: [...] ",
                "Syntax Error",
            ),
            (None, None),
            (
                "QueryBadFormed: A bad request has been sent to the endpoint: probably the SPARQL query is badly formed. \n\nResponse:\nb'Virtuoso 37000 Error SP031: SPARQL compiler: Internal error: Usupported combination of subqueries and service invocations\n\nSPARQL query:\n# use subclass to avoid timeout\n'",
                "Syntax Error",
            ),
            (
                "EndPointInternalError: The endpoint returned the HTTP status code 500. \n\nResponse:\nb'SPARQL-QUERY: queryStr=[...]java.util.concurrent.TimeoutException'",
                "Timeout",
            ),
        ]

        for error_msg, expected_category in test_cases:
            with self.subTest(error_msg=error_msg, expected_category=expected_category):
                error_filter = ErrorFilter(error_msg)
                self.assertEqual(
                    expected_category,
                    error_filter.category,
                    f"Failed for message: {error_msg}",
                )
                if self.debug:
                    print(f"Message: {error_msg}")
                    print(f"Category: {error_filter.category}")
                    print("---")

    @unittest.skipIf(Basetest.inPublicCI(), "needs import to run")
    def test_querystats_list(self):
        """
        test the query statistics list
        """
        qstats_list = QueryStatsList(name="query_statistics")
        qstats_records = self.nqm.sql_db.query("select * from QueryStats")
        for record in qstats_records:
            qstats = from_dict(data_class=QueryStats, data=record)
            qstats_list.stats.append(qstats)
        for qstats in qstats_list.stats:
            qstats.apply_error_filter()
            if self.debug:
                print(f"{qstats.endpoint_name}::{qstats.query_id}:{qstats.error_msg}")
                print(qstats.filtered_msg)

    def test_error_filter(self):
        """
        test the error filter
        """
        for raw_error_message, to_be_filtered, kept in self.example_errs:
            error_filter = ErrorFilter(raw_error_message)
            filtered_message = error_filter.get_message(for_html=False)
            if self.debug:
                print(filtered_message)
            self.assertTrue(to_be_filtered in raw_error_message)
            self.assertTrue(kept in raw_error_message)
            self.assertFalse(to_be_filtered in filtered_message)
            self.assertTrue(kept in filtered_message)

    def test_triply_db_errors(self):
        """
        test the _
        """
        error_log_path = Path(__file__).parent / "resources/error_messages"
        triplydb_path = error_log_path / "triplydb"
        error_msgs = [
            (
                triplydb_path / "parser_error.txt",
                "Syntax Error",
                "Invalid SPARQL query: Parser error on line 63:\n\n} AS %MOLS {\n-----^",
            ),
        ]
        for error_msg_path, expected_category, expected_msg in error_msgs:
            with self.subTest(error_msg=error_msg_path):
                error_msg = error_msg_path.read_text()
                error_filter = ErrorFilter(error_msg)
                self.assertEqual(expected_category, error_filter.category)
                self.assertEqual(expected_msg, error_filter.filtered_message)

    def test__extract_virtuoso_error(self):
        """
        test the _extract_virtuoso_error function
        """
        error_msg = """QueryBadFormed: A bad request has been sent to the endpoint: probably the SPARQL query is badly formed. Response: b'Virtuoso 37000 Error SP030: SPARQL compiler, line 0: Bad character \'%\' (0x25) in SPARQL expression at \'%\'\n\nSPARQL query:\n#output-format:application/sparql-results+json\n#\nPREFIX biopax: <http://www.biopax.org/release/biopax-level3.owl#>"""
        error_filter = ErrorFilter(error_msg)
        expected_filtered_error = (
            "Virtuoso 37000 Error SP030: SPARQL compiler, line 0: Bad character '%' (0x25) in SPARQL expression at '%'"
        )
        self.assertEqual(expected_filtered_error, error_filter.filtered_message)

    def test__blazegraph_error(self):
        """

        Returns:

        """
        error_log_path = Path(__file__).parent / "resources/error_messages"
        wdqs_path = error_log_path / "wdqs"
        error_msgs = [
            (
                wdqs_path / "duplicate_prefix.txt",
                "Syntax Error",
                "Multiple prefix declarations for prefix 'wd'",
            ),
            (wdqs_path / "timeout.txt", "Timeout", "Query has timed out."),
            (
                wdqs_path / "undefined_prefix.txt",
                "Syntax Error",
                "QName 'dcterms:isPartOf' uses an undefined prefix",
            ),
            (
                wdqs_path / "invalid_iri_declaration.txt",
                "Syntax Error",
                """Encountered " "<" "< "" at line 51, column 17.\nWas expecting:\n    <Q_IRI_REF> ...""",
            ),
            (
                wdqs_path / "invalid_sparql_syntax.txt",
                "Syntax Error",
                '''Lexical error at line 58, column 5.  Encountered: " " (32), after : "%"''',
            ),
        ]
        for error_msg_path, expected_category, expected_msg in error_msgs:
            with self.subTest(error_msg=error_msg_path):
                error_msg = error_msg_path.read_text()
                error_filter = ErrorFilter(error_msg)
                self.assertEqual(expected_category, error_filter.category)
                self.assertEqual(expected_msg, error_filter.filtered_message)

    def test_qlever_error_messages(self):
        """
        test the qlever error messages
        """
        error_log_path = Path(__file__).parent / "resources/error_messages"
        qlever_path = error_log_path / "qlever"
        error_msgs = [
            (
                qlever_path / "invalid_regex_func.txt",
                "Syntax Error",
                "Invalid SPARQL query: The second argument to the REGEX function must be a string literal (which contains the regular expression)",
            ),
            (
                qlever_path / "memory_limit.txt",
                "EndPointInternalError",
                "The memory limit was exceeded during the computation of a cross-product. Check if this cross-product is intentional or if you have mistyped a variable name.",
            ),
            (
                qlever_path / "invalid_literal.txt",
                "Syntax Error",
                "[json.exception.parse_error.101] parse error at line 1, column 1: syntax error while parsing value - invalid literal; last read: '<'",
            ),
            (
                qlever_path / "ask_unsupported.txt",
                "Syntax Error",
                "Not supported: ASK queries are currently not supported by QLever.",
            ),
        ]
        for error_msg_path, expected_category, expected_msg in error_msgs:
            with self.subTest(error_msg=error_msg_path):
                error_msg = error_msg_path.read_text()
                error_filter = ErrorFilter(error_msg)
                self.assertEqual(expected_category, error_filter.category)
                self.assertEqual(expected_msg, error_filter.filtered_message)

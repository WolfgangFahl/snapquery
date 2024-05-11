"""
Created on 2024-05-06

@author: wf
"""
from ngwidgets.basetest import Basetest

from snapquery.error_filter import ErrorFilter
from snapquery.snapquery_core import NamedQueryManager, QueryStats,QueryStatsList
from dacite import from_dict

class TestErrorFilter(Basetest):
    """
    test the error filter according to
    https://github.com/WolfgangFahl/snapquery/issues/20
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.nqm=NamedQueryManager()
        self.example_err_msgs = [
            """QueryBadFormed: A bad request has been sent to the endpoint: probably the SPARQL query is badly formed. Response: b'SPARQL-QUERY: queryStr=#\n#title: Variants of author name strings\nPREFIX target: \n\nSELECT \n (COUNT(?work) AS ?count)\n ?string\n (CONCAT("https://author-disambiguator.toolforge.org/names_oauth.php?doit=Look+for+author&name=", \n ENCODE_FOR_URI(?string)) AS ?author_resolver_url) \nWITH\n{\n # Find strings associated with the target author\n SELECT DISTINCT ?string_\n WHERE\n {\n { target: rdfs:label ?string_. } # in label\n UNION\n { target: skos:altLabel ?string_. } # in alias\n UNION\n {\n ?author_statement ps:P50 target: ; \n pq:P1932 ?string_. # in "stated as" strings for "author" statements on work items\n }\n }\n} AS %RAWstrings\nWITH\n# This part is due to Dipsacus fullonum, as per https://w.wiki/5Brk\n{\n # Calculate capitalization variants of these raw strings\n SELECT DISTINCT ?string\n WHERE\n {\n {\n INCLUDE %RAWstrings\n BIND(STR(?string_) AS ?string) # the raw strings\n }\n UNION\n {\n INCLUDE %RAWstrings\n BIND(UCASE(STR(?string_)) AS ?string) # uppercased versions of the raw strings\n }\n UNION\n {\n INCLUDE %RAWstrings\n BIND(LCASE(STR(?string_)) AS ?string) # lowercased versions of the raw strings\n }\n }\n} AS %NORMALIZEDstrings\nWHERE {\n # Find works that have "author name string" values equal to these normalized strings\n INCLUDE %NORMALIZEDstrings\n OPTIONAL { ?work wdt:P2093 ?string. }\n}\nGROUP BY ?string\nORDER BY DESC (?count)\n\nLIMIT 200\njava.util.concurrent.ExecutionException: org.openrdf.query.MalformedQueryException: Encountered " "<" "< "" at line 3, column 16.\nWas expecting:\n ...\n \n\tat java.util.concurrent.FutureTask.report(FutureTask.java:122)\n\tat java.util.concurrent.FutureTask.get(FutureTask.java:206)\n\tat com.bigdata.rdf.sail.webapp.BigdataServlet.submitApiTask(BigdataServlet.java:292)\n\tat com.bigdata.rdf.sail.webapp.QueryServlet.doSparqlQuery(QueryServlet.java:678)\n\tat com.bigdata.rdf.sail.webapp.QueryServlet.doPost(QueryServlet.java:275)\n\tat com.bigdata.rdf.sail.webapp.RESTServlet.doPost(RESTServlet.java:269)\n\tat com.bigdata.rdf.sail.webapp.MultiTenancyServlet.doPost(MultiTenancyServlet.java:195)\n\tat javax.servlet.http.HttpServlet.service(HttpServlet.java:707)\n\tat javax.servlet.http.HttpServlet.service(HttpServlet.java:790)\n\tat org.eclipse.jetty.servlet.ServletHolder.handle(ServletHolder.java:865)\n\tat org.eclipse.jetty.servlet.ServletHandler$CachedChain.doFilter(ServletHandler.java:1655)\n\tat org.wikidata.query.rdf.blazegraph.throttling.ThrottlingFilter.doFilter(ThrottlingFilter.java:320)\n\tat org.eclipse.jetty.servlet.ServletHandler$CachedChain.doFilter(ServletHandler.java:1642)\n\tat org.wikidata.query.rdf.blazegraph.throttling.SystemOverloadFilter.doFilter(SystemOverloadFilter.java:82)\n\tat org.eclipse.jetty.servlet.ServletHandler$CachedChain.doFilter(ServletHandler.java:1642)\n\tat ch.qos.logback.classic.helpers.MDCInsertingServletFilter.doFilter(MDCInsertingServletFilter.java:50)\n\tat org.eclipse.jetty.servlet.ServletHandler$CachedChain.doFilter(ServletHandler.java:1642)\n\tat org.wikidata.query.rdf.blazegraph.filters.QueryEventSenderFilter.doFilter(QueryEventSenderFilter.java:122)\n\tat org.eclipse.jetty.servlet.ServletHandler$CachedChain.doFilter(ServletHandler.java:1642)\n\tat org.wikidata.query.rdf.blazegraph.filters.ClientIPFilter.doFilter(ClientIPFilter.java:43)\n\tat org.eclipse.jetty.servlet.ServletHandler$CachedChain.doFilter(ServletHandler.java:1642)\n\tat org.wikidata.query.rdf.blazegraph.filters.JWTIdentityFilter.doFilter(JWTIdentityFilter.java:66)\n\tat org.eclipse.jetty.servlet.ServletHandler$CachedChain.doFilter(ServletHandler.java:1642)\n\tat org.wikidata.query.rdf.blazegraph.filters.RealAgentFilter.doFilter(RealAgentFilter.java:33)\n\tat org.eclipse.jetty.servlet.ServletHandler$CachedChain.doFilter(ServletHandler.java:1642)\n\tat org.wikidata.query.rdf.blazegraph.filters.RequestConcurrencyFilter.doFilter(RequestConcurrencyFilter.java:50)\n\tat org.eclipse.jetty.servlet.ServletHandler$CachedChain.doFilter(ServletHandler.java:1634)\n\tat org.eclipse.jetty.servlet.ServletHandler.doHandle(ServletHandler.java:533)\n\tat org.eclipse.jetty.server.handler.ScopedHandler.handle(ScopedHandler.java:146)\n\tat org.eclipse.jetty.security.SecurityHandler.handle(SecurityHandler.java:548)\n\tat org.eclipse.jetty.server.handler.HandlerWrapper.handle(HandlerWrapper.java:132)\n\tat org.eclipse.jetty.server.handler.ScopedHandler.nextHandle(ScopedHandler.java:257)\n\tat org.eclipse.jetty.server.session.SessionHandler.doHandle(SessionHandler.java:1595)\n\tat org.eclipse.jetty.server.handler.ScopedHandler.nextHandle(ScopedHandler.java:255)\n\tat org.eclipse.jetty.server.handler.ContextHandler.doHandle(ContextHandler.java:1340)\n\tat org.eclipse.jetty.server.handler.ScopedHandler.nextScope(ScopedHandler.java:203)\n\tat org.eclipse.jetty.servlet.ServletHandler.doScope(ServletHandler.java:473)\n\tat org.eclipse.jetty.server.session.SessionHandler.doScope(SessionHandler.java:1564)\n\tat org.eclipse.jetty.server.handler.ScopedHandler.nextScope(ScopedHandler.java:201)\n\tat org.eclipse.jetty.server.handler.ContextHandler.doScope(ContextHandler.java:1242)\n\tat org.eclipse.jetty.server.handler.ScopedHandler.handle(ScopedHandler.java:144)\n\tat org.eclipse.jetty.server.handler.ContextHandlerCollection.handle(ContextHandlerCollection.java:220)\n\tat org.eclipse.jetty.server.handler.HandlerCollection.handle(HandlerCollection.java:126)\n\tat org.eclipse.jetty.server.handler.HandlerWrapper.handle(HandlerWrapper.java:132)\n\tat org.eclipse.jetty.server.Server.handle(Server.java:503)\n\tat org.eclipse.jetty.server.HttpChannel.handle(HttpChannel.java:364)\n\tat org.eclipse.jetty.server.HttpConnection.onFillable(HttpConnection.java:260)\n\tat org.eclipse.jetty.io.AbstractConnection$ReadCallback.succeeded(AbstractConnection.java:305)\n\tat org.eclipse.jetty.io.FillInterest.fillable(FillInterest.java:103)\n\tat org.eclipse.jetty.io.ChannelEndPoint$2.run(ChannelEndPoint.java:118)\n\tat org.eclipse.jetty.util.thread.strategy.EatWhatYouKill.runTask(EatWhatYouKill.java:333)\n\tat org.eclipse.jetty.util.thread.strategy.EatWhatYouKill.doProduce(EatWhatYouKill.java:310)\n\tat org.eclipse.jetty.util.thread.strategy.EatWhatYouKill.tryProduce(EatWhatYouKill.java:168)\n\tat org.eclipse.jetty.util.thread.strategy.EatWhatYouKill.run(EatWhatYouKill.java:126)\n\tat org.eclipse.jetty.util.thread.ReservedThreadExecutor$ReservedThread.run(ReservedThreadExecutor.java:366)\n\tat org.eclipse.jetty.util.thread.QueuedThreadPool.runJob(QueuedThreadPool.java:765)\n\tat org.eclipse.jetty.util.thread.QueuedThreadPool$2.run(QueuedThreadPool.java:683)\n\tat java.lang.Thread.run(Thread.java:750)\nCaused by: org.openrdf.query.MalformedQueryException: Encountered " "<" "< "" at line 3, column 16.\nWas expecting:\n ...\n \n\tat com.bigdata.rdf.sail.sparql.Bigdata2ASTSPARQLParser.parseQuery2(Bigdata2ASTSPARQLParser.java:400)\n\tat com.bigdata.rdf.sail.webapp.QueryServlet$SparqlQueryTask.call(QueryServlet.java:741)\n\tat com.bigdata.rdf.sail.webapp.QueryServlet$SparqlQueryTask.call(QueryServlet.java:695)\n\tat com.bigdata.rdf.task.ApiTaskForIndexManager.call(ApiTaskForIndexManager.java:68)\n\tat java.util.concurrent.FutureTask.run(FutureTask.java:266)\n\tat java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)\n\tat java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)\n\t... 1 more\nCaused by: com.bigdata.rdf.sail.sparql.ast.ParseException: Encountered " "<" "< "" at line 3, column 16.\nWas expecting:\n ...\n \n\tat com.bigdata.rdf.sail.sparql.ast.SyntaxTreeBuilder.generateParseException(SyntaxTreeBuilder.java:9722)\n\tat com.bigdata.rdf.sail.sparql.ast.SyntaxTreeBuilder.jj_consume_token(SyntaxTreeBuilder.java:9589)\n\tat com.bigdata.rdf.sail.sparql.ast.SyntaxTreeBuilder.IRI(SyntaxTreeBuilder.java:7527)\n\tat com.bigdata.rdf.sail.sparql.ast.SyntaxTreeBuilder.PrefixDecl(SyntaxTreeBuilder.java:296)\n\tat com.bigdata.rdf.sail.sparql.ast.SyntaxTreeBuilder.Prolog(SyntaxTreeBuilder.java:257)\n\tat com.bigdata.rdf.sail.sparql.ast.SyntaxTreeBuilder.QueryContainer(SyntaxTreeBuilder.java:215)\n\tat com.bigdata.rdf.sail.sparql.ast.SyntaxTreeBuilder.parseQuery(SyntaxTreeBuilder.java:32)\n\tat com.bigdata.rdf.sail.sparql.Bigdata2ASTSPARQLParser.parseQuery2(Bigdata2ASTSPARQLParser.java:336)\n\t... 7 more\n'"""
        ]
        
    def test_querystats_list(self):
        """
        test the query statistics list
        """
        qstats_list=QueryStatsList(name="query_statistics")
        qstats_records=self.nqm.sql_db.query("select * from QueryStats")
        for record in qstats_records:
            qstats = from_dict(data_class=QueryStats,data=record)
            qstats_list.stats.append(qstats)
        for qstats in qstats_list.stats:
            qstats.apply_error_filter()
            if self.debug:
                print(qstats.error_msg)
                print(qstats.filtered_msg)

    def test_error_filter(self):
        """
        test the error filter
        """
        for raw_error_message in self.example_err_msgs:
            error_filter = ErrorFilter(raw_error_message)
            filtered_message = error_filter.get_message()
            if self.debug:
                print(filtered_message)
            self.assertTrue("com.bigdata" in raw_error_message)
            self.assertFalse("com.bigdata" in filtered_message)
            self.assertTrue("SELECT <br>" in filtered_message)

from django.shortcuts import render
from django.http import HttpResponse
import os,re,exceptions,logging
from . import analyzer

logger = logging.getLogger('faxlog.views')

error_msg = """
There is something wrong with your log file, if you have any comments for this tool, pls contact with jason.a.sun@nokia-sbell.com
"""

# Create your views here.
def diagram(request):
    context = {}
    return render(request, 'analyzer/diagram.html', context)


def index(request):
    context = {}
    if request.method == "POST":
        f = request.FILES.get("log")
        requestIP = request.META['REMOTE_ADDR']
        baseDir = os.path.dirname(os.path.abspath(__file__));
        logDir = os.path.join(baseDir,'static','logs');
        fileName = os.path.join(logDir,requestIP)

        fobj = open(fileName,"wb")
        for chunk in f.chunks():
            fobj.write(chunk)

        fobj.close()
        analyzer.analyze(fileName)

        try:
            logfile = open(fileName+"_analyzed")
            fax_log = logfile.read()
        except Exception as e:
            logger.error("exception occurred:" + e)
        finally:
            logfile.close()

        if fax_log:
            context={"fax_log":fax_log}
        else:
            context = {"error_msg":error_msg}

        return render(request, 'analyzer/diagram.html', context)
    else:
        return render(request, 'analyzer/index.html', context)

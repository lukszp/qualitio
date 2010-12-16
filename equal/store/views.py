from mptt.models import MPTTModel

from django.views.generic.simple import direct_to_template
from django.core.exceptions import ObjectDoesNotExist
from django.utils import simplejson as json
from django.http import HttpResponse

from equal.core.utils import json_response, success, failed
from equal.store.models import TestCaseDirectory, TestCase
from equal.store.forms import TestCaseForm, TestCaseDirectoryForm, AttachmentFormSet, TestCaseStepFormSet, GlossaryWord

def index(request):
    return direct_to_template(request, 'store/base.html', {})

def directory_details(request, directory_id): 
    return direct_to_template(request, 'store/testcasedirectory_details.html',
                              {'directory' : TestCaseDirectory.objects.get(pk=directory_id)})

def directory_edit(request, directory_id):
    directory = TestCaseDirectory.objects.get(pk=directory_id)
    testcasedirectory_form = TestCaseDirectoryForm(instance=directory)
    return direct_to_template(request, 'store/testcasedirectory_edit.html',
                              {'directory' : directory, 
                               'testcasedirectory_form' : testcasedirectory_form })

def testcase_details(request, testcase_id):
    return direct_to_template(request, 'store/testcase_details.html',
                              {'testcase' : TestCase.objects.get(pk=testcase_id)})

def testcase_edit(request, testcase_id):
    testcase = TestCase.objects.get(pk=testcase_id)
    testcase_form = TestCaseForm(instance=testcase)
    testcasesteps_form = TestCaseStepFormSet(instance=testcase)
    glossary_word_search_form = GlossaryWord()
    return direct_to_template(request, 'store/testcase_edit.html',
                              { 'testcase' : testcase,
                                'testcase_form' : testcase_form,
                                'testcasesteps_form' : testcasesteps_form,
                                'glossary_word_search_form' : glossary_word_search_form })

@json_response
def testcase_valid(request, testcase_id):
    testcase = TestCase.objects.get(pk=str(testcase_id))
    testcase_form = TestCaseForm(request.POST, instance=testcase)
    testcasesteps_form = TestCaseStepFormSet(request.POST, instance=testcase)
    if testcase_form.is_valid() and testcasesteps_form.is_valid(): 
        testcase_form.save()
        testcasesteps_form.save()
        return success(message='TestCase saved', 
                       data={ "parent_id" : getattr(testcase.parent,"id", 0), 
                              "current_id" : testcase.id })
    else:
        
        return failed(message="Validation errors", 
                      data=[(k, v[0]) for k, v in testcase_form.errors.items()])


def testcase_attachments(request, testcase_id):
    testcase = TestCase.objects.get(pk=testcase_id)
    attachments_form = AttachmentFormSet(instance=testcase)
    return direct_to_template(request, 'store/testcase_attachments.html',
                              {'testcase' : testcase,
                               'attachments_form' : attachments_form})

def to_tree_element(object, type):
    state = "closed" if isinstance(object, MPTTModel) else ""
    return { 'attr' : {'id' : "%s_%s" % (object.pk, type),
                       'rel' : type},
             'data' : object.name,
             'state' : state }


def get_children(request):
    data = []

    try:
        node_id = int(request.GET.get('id', 0))
        node = TestCaseDirectory.objects.get(pk=node_id)
        directories = node.get_children()
        files = node.testcase_set.all()

    except (ObjectDoesNotExist, ValueError):
        directories = TestCaseDirectory.tree.root_nodes()
        files = TestCase.objects.filter(parent=None)
    
    data = map(lambda x: to_tree_element(x, x._meta.module_name), directories)+\
        map(lambda x: to_tree_element(x,x._meta.module_name), files)

    return HttpResponse(json.dumps(data), mimetype="application/json")

from AccessControl import getSecurityManager
from AccessControl import Unauthorized
import json
import inspect
from zope.interface import implements
from zope.component import queryUtility
from zope.component import getMultiAdapter
from zope.schema.interfaces import IVocabularyFactory
from Products.Five import BrowserView
from plone.app.widgets.interfaces import IWidgetsView


_permissions = {
    'plone.app.vocabularies.Users': 'Modify portal content',
    'plone.app.vocabularies.catalog': 'View'
}


class WidgetsView(BrowserView):
    """A view that gives access to various widget related functions.
    """

    implements(IWidgetsView)

    def getVocabulary(self):
        """
        """
        self.request.response.setHeader("Content-type", "application/json")

        factory_name = self.request.get('name', None)
        if not factory_name:
            return json.dumps({'error': 'No factory provided.'})
        if factory_name not in _permissions:
            return json.dumps({'error': 'Vocabulary lookup not allowed'})
        sm = getSecurityManager()
        if not sm.checkPermission(_permissions[factory_name], self.context):
            raise Unauthorized('You do not have permission to use this vocabulary')
        factory = queryUtility(IVocabularyFactory, factory_name)
        if not factory:
            return json.dumps({
                'error': 'No factory with name "%s" exists.' % factory_name})

        # check if factory excepts query argument
        query = self.request.get('query', '')
        if query.startswith('{') and query.endswith('}'): # detect if json
            query = json.loads(query)
        factory_spec = inspect.getargspec(factory.__call__)
        if query and len(factory_spec.args) >= 3 and \
                factory_spec.args[2] == 'query':
            vocabulary = factory(self.context, query)
        else:
            vocabulary = factory(self.context)

        items = []
        attrs = 'attributes' in query and query['attributes']
        if attrs:
            item = {}
            for vocab_item in vocabulary:
                for attr in attrs:
                    vocab_value = vocab_item.value
                    item[attr] = getattr(vocab_value, attr, None)
                items.append(item)
        else:
            for item in vocabulary:
                items.append({'id': item.token, 'text': item.title})

        # TODO: add option for limiting number of results
        # TODO: add option for batching
        # TODO: add option for sorting

        return json.dumps({'results': items})

    def bodyDataOptions(self):
        portal_state = getMultiAdapter(
            (self.context, self.request), name=u'plone_portal_state')
        return {
            'data-portal-navigation-url': portal_state.navigation_root_url(),
            'data-portal-url': portal_state.portal_url(),
            'data-context-url': self.context.absolute_url(),
            'data-pattern': 'plone-tabs',
        }

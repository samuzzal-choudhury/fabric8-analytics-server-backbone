
def add_resource_no_matter_slashes(resource, route, endpoint=None, defaults=None):
    """Adds a resource for both trailing slash and no trailing slash to prevent redirects.
    """
    slashless = route.rstrip('/')
    _resource_paths.append(api_v1.url_prefix + slashless)
    slashful = route + '/'
    endpoint = endpoint or resource.__name__.lower()
    defaults = defaults or {}

    rest_api_v1.add_resource(resource,
                             slashless,
                             endpoint=endpoint + '__slashless',
                             defaults=defaults)
    rest_api_v1.add_resource(resource,
                             slashful,
                             endpoint=endpoint + '__slashful',
                             defaults=defaults)


class ResourceWithSchema(Resource):
    """This class makes sure we can add schemas to any response returned by any API endpoint.

    If a subclass of ResourceWithSchema is supposed to add a schema, it has to:
    - either implement `add_schema` method (see its docstring for information on signature
      of this method)
    - or add a `schema_ref` (instance of `f8a_worker.schemas.SchemaRef`) class attribute.
      If this attribute is added, it only adds schema to response with `200` status code
      on `GET` request.
    Note that if both `schema_ref` and `add_schema` are defined, only the method will be used.
    """

    def add_schema(self, response, status_code, method):
        """Add schema to response. The schema must be dict containing 3 string values:
        name, version and url (representing name and version of the schema and its
        full url).

        :param response: dict, the actual response object returned by the view
        :param status_code: int, numeric representation of returned status code
        :param method: str, uppercase textual representation of used HTTP method
        :return: dict, modified response object that includes the schema
        """
        if hasattr(self, 'schema_ref') and status_code == 200 and method == 'GET':
            response['schema'] = {
                'name': self.schema_ref.name,
                'version': self.schema_ref.version,
                'url': PublishedSchemas.get_api_schema_url(name=self.schema_ref.name,
                                                           version=self.schema_ref.version)
            }
        return response

    def dispatch_request(self, *args, **kwargs):
        response = super().dispatch_request(*args, **kwargs)

        method = request.method
        status_code = 200
        response_body = response
        headers = None

        if isinstance(response, tuple):
            response_body = response[0]
            if len(response) > 1:
                status_code = response[1]
            if len(response) > 2:
                headers = response[2]

        return self.add_schema(response_body, status_code, method), status_code, headers


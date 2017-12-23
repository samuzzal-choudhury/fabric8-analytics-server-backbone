from resource import ResourceWithSchema

class StackAggreagor(ResourceWithSchema):
    @staticmethod
    def post(ecosystem):
        if not ecosystem:
            raise HTTPError(400, error="Expected ecosystem in the request")

        decoded = decode_token()

        pkg = get_next_component_from_graph(
            ecosystem,
            decoded.get('email'),
            decoded.get('company'),
        )
        if pkg:
            return pkg[0]
        else:
            raise HTTPError(200, error="No package found for tagging.")

from .base import GLSRequestBody


class ParcelLabelGenerator:

    def __init__(self, request_body: GLSRequestBody):
        self.request_body = request_body

    def preprocess_input_data(self):
        # TODO: Input data preprocessing
        pass

    def generate_label(self):
        # TODO: Generate label via API call
        pass
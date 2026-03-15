# Approach 3:
# Here we have abstract class DocumentElement which has render method and subclasses like TextElement, ImageElement, TableElement, etc.
# Document class which has list of DocumentElements and add element method and get element method.
# Document Renderer class which has render method and renders the document.
# Document Persistance class which has save method and saves the document.
# Document Editor class which has add_text and add_image methods 
# Document Client class which has main method and creates instance of DocumentEditor class, document renderer and document persistance and calls the add_text and add_image methods.

from abc import ABC, abstractmethod

class DocumentElement(ABC):
    @abstractmethod
    def render(self):
        pass

class TextElement(DocumentElement):
    def __init__(self, text):
        self.text = text
    def render(self):
        return self.text

class ImageElement(DocumentElement):
    def __init__(self, path):
        self.path = path
    def render(self):
        return f"<img src='{self.path}' alt='{self.path}' />"

class TableElement(DocumentElement):
    def __init__(self, rows):
        self.rows = rows
    def render(self):
        return f"<table>{self.rows}</table>"

class NewLineElement(DocumentElement):
    def __init__(self):
        pass
    def render(self):
        return "\n"

class Persistance(ABC):
    @abstractmethod
    def save(self, document):
        pass

class SaveToFile(Persistance):
    def __init__(self, path):
        self.path = path
    def save(self, document):
        with open(self.path, 'w') as f:
            f.write(document)

class SaveToDatabase(Persistance):
    def __init__(self, database_name):
        self.database_name = database_name
    def save(self, document):
        # Write code to save document to database
        print(f"Saving document to database: {self.database_name}")


class Document:
    def __init__(self):
        self.elements = []
    def add_element(self, element: DocumentElement):
        self.elements.append(element)
    def get_elements(self) -> list[DocumentElement]:
        return self.elements
    def render(self) -> str:
        result = ""
        for element in self.elements:
            result += element.render()
        return result

class DocumentRenderer:
    def __init__(self, document: Document):
        self.document = document
    def render(self) -> str:
        result = ""
        for element in self.document.elements:
            result += element.render()
        return result

class DocumentEditor:
    def __init__(self, document: Document):
        self.document = document
    def add_text(self, text: str):
        self.document.add_element(TextElement(text))
    def add_image(self, path: str):
        self.document.add_element(ImageElement(path))
    def add_new_line(self):
        self.document.add_element(NewLineElement())

# Client usage Example:
if __name__ == "__main__":
    document = Document()
    document_renderer = DocumentRenderer(document)
    persistance = SaveToFile("document.html")
    document_editor = DocumentEditor(document)
    document_editor.add_text("Hello, world!")
    document_editor.add_image("image.png")
    document_editor.add_new_line()
    document_editor.add_text("This is a new line")
    rendered_document = document_renderer.render()
    persistance.save(rendered_document)

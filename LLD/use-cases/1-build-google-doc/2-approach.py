# Approach 2:
# Here we have abstract class DocumentElement which has render method and subclasses like TextElement, ImageElement, TableElement, etc.
# Document class which has list of DocumentElements and has render method.
# persistance abstract class which has save method and subclasses like SaveTOFile, SaveToDatabase
# DocumentEditor class which has add_text and add_image methods and calls the render method of Document class and save method of persistance class.
# Client class which has main method and creates instance of DocumentEditor class and calls the add_text and add_image methods.


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

    def render(self) -> str:
        result = ""
        for element in self.elements:
            result += element.render()
        return result

class DocumentEditor:
    def __init__(self, document: Document, persistance: Persistance):
        self.document = document
        self.persistance = persistance
        self.rendered_document = None
    def add_text(self, text: str):
        self.document.add_element(TextElement(text))
    def add_image(self, path: str):
        self.document.add_element(ImageElement(path))
    def add_new_line(self):
        self.document.add_element(NewLineElement())
    def render(self) -> str:
        self.rendered_document =  self.document.render()
    def save(self):
        self.render()
        self.persistance.save(self.rendered_document)

# Client usage Example:
if __name__ == "__main__":
    document = Document()
    persistance = SaveToFile("document.html")
    document_editor = DocumentEditor(document, persistance)
    document_editor.add_text("Hello, world!")
    document_editor.add_image("image.png")
    document_editor.add_new_line()
    document_editor.add_text("This is a new line")
    document_editor.save()


# Drawbacks:
# 1. Single responsibility principle: The DocumentEditor class is responsible for both adding text and images to the document, and rendering the document. This violates the single responsibility principle.
# 2. Open/closed principle: The DocumentEditor class is not open for extension but for modification. If we want to add a new feature, we need to modify the DocumentEditor class.
# 3. Dependency inversion principle: The DocumentEditor class depends on the Persistance class. If we want to change the persistance method, we need to modify the DocumentEditor class.

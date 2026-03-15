# Approach 1:
# In this approach, we are using a single class to handle all the document editing operations.
# Document Editor class:
# list<String> document
# void add_text(String text)
# void add_image(String path)
# void render_doc()
# void save_doc(String path)


class DocumentEditor:
    def __init__(self):
        self.document = []
        self.rendered_document = None

    def add_text(self, text):
        self.document.append(text)

    def add_image(self, path):
        self.images.append(path)

    def render_doc(self) -> str: 
        if self.rendered_document is not None:
            result = ""
            for line in self.document:
                if line.endswith(".png") or line.endswith(".jpg") or line.endswith(".jpeg"):
                    result += f"<img src='{line}' alt='{line}' />\n"
                else:
                    result += line + "\n"
            return result
        return self.rendered_document

    def save_doc(self, path):
        with open(path, 'w') as f:
            f.write(self.rendered_document)
if __name__ == "__main__":
    editor = DocumentEditor()
    editor.add_text("Hello, world!")
    editor.add_image("image.png")
    editor.render_doc()
    editor.save_doc("document.html")
    print(editor.rendered_document)

# Drawbacks
# 1. Single responsibility principle: The DocumentEditor class is responsible for both adding text and images to the document, and rendering the document. This violates the single responsibility principle.
# 2. Open/closed principle: The DocumentEditor class is not open for extension but for modification. If we want to add a new feature, we need to modify the DocumentEditor class.
# 3. Dependency inversion principle: The DocumentEditor class depends on the HTMLRenderer class. If we want to change the rendering engine, we need to modify the DocumentEditor class.
# 4. Liskov substitution principle: The DocumentEditor class is not a subclass of the Document class. This violates the liskov substitution principle.
# 5. Interface segregation principle: The DocumentEditor class is not a subclass of the Document class. This violates the interface segregation principle.
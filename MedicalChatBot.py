####    OPEN AI   ##### Charged for every run  ####
# Medical charbot provides Remedies for Patient's questions

#pip install openai

# Upload "Gale Encyclopedia of Medicine Vol. 4 (N-S).pdf" on the left under content folder
import openai
from openai import OpenAI

client = OpenAI(api_key = "sk-proj-ER3f94bRGEnuonIUERBOB34Y3J")

assistant = client.beta.assistants.create(
  name="A-ZMedicalCure",
  instructions=" You are a Doctor who can help patients with remedies. Use your knowledge base to answer questions anyone might have.",
  model="gpt-4o",
  tools=[{"type": "file_search"}],
)

# Create a vector store caled "A-Z Medical Cure"
vector_store = client.beta.vector_stores.create(name="A-ZMedicalCure")

# Ready the files for upload to OpenAI
file_paths = ["Gale Encyclopedia of Medicine Vol. 4 (N-S).pdf"]
file_streams = [open(path, "rb") for path in file_paths]

# Use the upload and poll SDK helper to upload the files, add them to the vector store,
# and poll the status of the file batch for completion.
file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
  vector_store_id=vector_store.id, files=file_streams
)

# You can print the status and the file counts of the batch to see the result of this operation.
print(file_batch.status)
print(file_batch.file_counts)

from google.colab import drive
drive.mount('/content/drive')

assistant = client.beta.assistants.update(
  assistant_id=assistant.id,
  tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
)

message_file = client.files.create(
  file=open("Gale Encyclopedia of Medicine Vol. 4 (N-S).pdf", "rb"), purpose="assistants"
)

# Create a thread and attach the file to the message
thread = client.beta.threads.create(
  messages=[
    {
      "role": "user",
      "content": """I am a Doctor at a local Hospital and a patient will ask you the questions.
                  Make sure you respond in a gentle way. Do not tell the user to do anything, just ask for Symptoms and suggest.
       First tell the user that you can provide them with simple remedies.

       Then ask them for their Age and Gender and what is their issue today.

        Let the user respond or ask questions, do not provide any info until they do.
        Only provide them with information from the filename""",
      # Attach the new file to the message.
      "attachments": [
        { "file_id": message_file.id, "tools": [{"type": "file_search"}] }

      ],
    }
  ]
)

# The thread now has a vector store with that file in its tool resources.
print(thread.tool_resources.file_search)
#print(message_file,id)

run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id, assistant_id=assistant.id
)

messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))

message_content = messages[0].content[0].text
annotations = message_content.annotations
citations = []
for index, annotation in enumerate(annotations):
    message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
    if file_citation := getattr(annotation, "file_citation", None):
        cited_file = client.files.retrieve(file_citation.file_id)
        citations.append(f"[{index}] {cited_file.filename}")

print(message_content.value)
print("\n".join(citations))

i = 0
while i < 10:
  userInput = input("Send a message")

  thread_message = client.beta.threads.messages.create(
    thread.id,
    role="user",
    content= userInput,
  )


  run = client.beta.threads.runs.create_and_poll(
      thread_id=thread.id, assistant_id=assistant.id
  )

  messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))

  message_content = messages[0].content[0].text
  annotations = message_content.annotations
  citations = []
  for index, annotation in enumerate(annotations):
      message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
      if file_citation := getattr(annotation, "file_citation", None):
          cited_file = client.files.retrieve(file_citation.file_id)
          citations.append(f"[{index}] {cited_file.filename}")

  print(message_content.value)
  print("\n".join(citations))
  i=i+1

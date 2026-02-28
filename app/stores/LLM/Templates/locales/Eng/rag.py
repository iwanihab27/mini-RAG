from string import Template


#### RAG PROMPTS ####

#### System ####

system_prompt =Template("\n".join([
            "you are an assistant to generate a response for the user .",
         
            "you will be provided a set of documents .",
         
            "you have to generate a response based on the documents provided.",

            "you can apologize if you do not know the answer.",

            "you have to generate response in the same language as the user's query"
         
        ]))

#### Document ####

document_prompt =Template(
    "\n".join([
    "## Document No: $doc_num",
    "### Content: $chunk_text",
    ])
)

#### Footer ####

footer_prompt =Template("\n".join([
    "Based only on the above documents, please generate answer for the user.",
    "## question:"
    "$query,"
    "",
    "### Answer:",
])
)
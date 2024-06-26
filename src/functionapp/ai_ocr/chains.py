from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from langchain_core.prompts import HumanMessagePromptTemplate

from ai_ocr.azure.openai_ops import get_llm

import logging

def get_structured_data(pages: str, prompt: str, json_schema: str, images=[]) -> any:
    messages = [
        ("system",
         prompt
         ),
        ("human", "{input}"),
        ("human", "{schema}"),
    ]

    schema_prompt = """
    The output should be formatted as a JSON instance that conforms to the JSON schema template below. RETURN ONLY THE JSON schema template filled with data from the document and no other comments.

    As an example, for the schema {"properties": {"foo": {"title": "Foo", "description": "a list of strings", "type": "array", "items": {"type": "string"}}}, "required": ["foo"]}
    the object {"foo": ["bar", "baz"]} is a well-formatted instance of the schema. The object {"properties": {"foo": ["bar", "baz"]}} is not well-formatted. If JSON schema template
    is empty, then create a structure that you think is appropriate for the given document.

    Here is the JSON schema template:
    ```""" + str(json_schema) + "```"

    prompt = ChatPromptTemplate.from_messages(messages)
    if len(images) > 0:
        prompt.append(HumanMessage("There are also images available that you can use to verify the ocr information: "))
        logging.debug("There are also images available that you can use to verify the ocr information:")
    for img in images:
        logging.debug("Adding 1 image to the prompt...")
        prompt.append(
            HumanMessage(content=[{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}}]))
    prompt.append('The JSON object extracted is:\n\n')    
    model = get_llm()
    chain = prompt | model
    return chain.invoke({"input": pages, "schema": schema_prompt})



def get_summary_with_gpt(mkd_output_json: str) -> any:
    reasoning_prompt = """
    Use the provided data represented in the schema to produce a summary in natural language. The format should be a few sentences summary of the document.

    As an example, for the schema {"properties": {"foo": {"title": "Foo", "description": "a list of strings", "type": "array", "items": {"type": "string"}}}, "required": ["foo"]}
    the object {"foo": ["bar", "baz"]} is a well-formatted instance of the schema. The object {"properties": {"foo": ["bar", "baz"]}} is not well-formatted.
    """
    
    chat_template = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=(
                    reasoning_prompt
                )
            ),
            HumanMessagePromptTemplate.from_template("{text}"),
        ]
    )
    messages = chat_template.format_messages(text=mkd_output_json)

    model = get_llm()
    return model.invoke(messages)


def classify_doc_with_llm(ocr_input: str, classification_system_prompt) -> any:
    prompt = classification_system_prompt
    
    chat_template = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=(
                    prompt
                )
            ),
            HumanMessagePromptTemplate.from_template("{text}"),
        ]
    )
    messages = chat_template.format_messages(text=ocr_input)

    model = get_llm()
    return model.invoke(messages)
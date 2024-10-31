SUMMARIZE = """
**INSTRUCTIONS**\n
Please provide a comprehensive summary of the provided text, capturing all key details and arguments. The summary should accurately reflect the main message of the original content, focusing on critical points while maintaining a semi-formal tone. It is important that the summary includes all essential information to allow a clear understanding of the article or news piece without reading the original text. Please ensure the language remains objective and factual, avoiding personal biases. Deliver the summary concisely, aiming to include all necessary information within a succinct format. The summary must be written in English. Take a deep breath and work on this step-by-step.
\n\n
**RETURN FORMAT**\n
Please return only the summary list without any your additional text on.
\n\n
Example:
\n\n
* Summary piece
* Summary piece
* Summary piece

"""

SUMMARIZE_SEVERAL = """
**SUMMARY INSTRUCTIONS**\n
There are dictionary with several articles here. Samarize the text of each into a brief and objective presentation. Capture all key points, arguments, and critical information. The summary must be written in English.
\n\n
**RETURN FORMAT**\n
Return ONLY ONE tuple that will contain complete brief without any yor additional text on. If there was no value in the original dictionary, leave it empty in the tuple as well.
\n\n
An Output Example like:
\n\n
("...", "...", "...")
"""

SUMMARIZE_ONE = """
Please give a short summary overview of the given text. Not over 300 characters, in plain English, in an easy-to-understand format. \n\n
Return only the samarization, in a few sentences (not a list), without any additional text not related to the source material. The summary must be written in English. 
"""

COMPARE_TITLES = """
**INSTRUCTIONS**\n
Please analyze and determine which article titles from the list discuss about **the same**. Evaluate them based on their **meaning**, not just keywords. Please be extremely careful. Do not include item if you are not sure.\n\n

Take a deep breath and work on this step-by-step.



**RETURN FORMAT**\n\n

Return only a tuple of lists of similar articles, without repetition (for example, ([...,...], [...,...])) or None if there are no matches. If a title has no matches, do not include its number in the tuple as a single element of the list. Do not add any comments or extraneous text from yourself.\n\n


"""

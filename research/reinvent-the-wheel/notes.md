Some code that almost worked, incase I need it later:
```

    # def _get_llm(self) -> ChatOpenAI:
    #     """ Set up the LLM with needed arguments """
    #     llm = ChatOpenAI(
    #         temperature=0,
    #         streaming=True,
    #         callbacks=[print],
    #         #, model="gpt-4")
    #     )
    #     return llm



        # llm_chain = LLMChain(
        #     llm=self.llm,
        #     prompt=PromptTemplate.from_template("{prompt}"),
        # )
        #
        # print(llm_chain.run(prompt))
        #



    class States(Enum):
        """
            The language model at any point should be writing to any one of these fields.
            Since the ScratchPad gets new text chunk by chunk, this state keeps track of which
            field is currently being appended to.
        """
        THOUGHT = 0
        ACTION = 1
        ACTION_INPUT = 2
        FINISH = 3

```

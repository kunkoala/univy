# Mock Prompts Guide for Swagger UI

This guide shows you how to create mock prompts for testing the RAG API endpoints in Swagger UI.

## Available Endpoints

1. **POST /rag/query** - Standard query endpoint
2. **POST /rag/query/stream** - Streaming query endpoint

## QueryRequest Model Structure

```json
{
  "query": "string",
  "mode": "hybrid",
  "only_need_context": false,
  "only_need_prompt": false,
  "response_type": "string",
  "top_k": 5,
  "max_token_for_text_unit": 1000,
  "max_token_for_global_context": 2000,
  "max_token_for_local_context": 2000,
  "conversation_history": [
    {
      "role": "user",
      "content": "string"
    },
    {
      "role": "assistant", 
      "content": "string"
    }
  ],
  "history_turns": 2,
  "ids": ["string"],
  "user_prompt": "string"
}
```

## Mock Prompt Examples

### 1. Basic Query
```json
{
  "query": "What are the main topics discussed in the uploaded documents?",
  "mode": "hybrid"
}
```

### 2. Context-Only Query
```json
{
  "query": "Find information about mobility measurement in orthopedics",
  "mode": "hybrid",
  "only_need_context": true,
  "top_k": 3
}
```

### 3. Prompt-Only Query
```json
{
  "query": "Explain the validation study methodology",
  "mode": "hybrid",
  "only_need_prompt": true,
  "response_type": "Multiple Paragraphs"
}
```

### 4. Conversation with History
```json
{
  "query": "Can you elaborate on the reliability measures mentioned earlier?",
  "mode": "hybrid",
  "conversation_history": [
    {
      "role": "user",
      "content": "What are the reliability measures in the study?"
    },
    {
      "role": "assistant",
      "content": "The study discusses several reliability measures including test-retest reliability and inter-rater reliability."
    }
  ],
  "history_turns": 1
}
```

### 5. Specific Document Query
```json
{
  "query": "What are the key findings about telemonitoring?",
  "mode": "local",
  "ids": ["validation_study_telemonitor.pdf"],
  "top_k": 5,
  "response_type": "Bullet Points"
}
```

### 6. Token-Limited Query
```json
{
  "query": "Summarize the VVAFER paper",
  "mode": "hybrid",
  "max_token_for_text_unit": 500,
  "max_token_for_global_context": 1000,
  "max_token_for_local_context": 1000,
  "response_type": "Single Paragraph"
}
```

### 7. Custom Prompt Query
```json
{
  "query": "Analyze the methodology section",
  "mode": "hybrid",
  "user_prompt": "Please provide a detailed analysis of the methodology section, focusing on the research design, data collection methods, and statistical analysis approach.",
  "response_type": "Multiple Paragraphs"
}
```

### 8. Resume Analysis Query
```json
{
  "query": "What are the key skills and experience mentioned in the resume?",
  "mode": "hybrid",
  "ids": ["Resume_Azhar_En_07042025_SWE.pdf"],
  "response_type": "Bullet Points"
}
```

## Mode Options

- **`hybrid`** (default): Combines local and global retrieval
- **`local`**: Entity-based retrieval
- **`global`**: Relationship-based retrieval  
- **`naive`**: Simple retrieval without advanced processing
- **`mix`**: Mixed retrieval strategy
- **`bypass`**: Bypass retrieval, use only LLM

## Response Types

- **`Multiple Paragraphs`**: Detailed multi-paragraph response
- **`Single Paragraph`**: Concise single paragraph
- **`Bullet Points`**: Structured bullet point format

## Testing Tips

1. **Start Simple**: Use basic queries first to test connectivity
2. **Test Different Modes**: Try each mode to see how results differ
3. **Use Context Flags**: Test `only_need_context` and `only_need_prompt` to understand the pipeline
4. **Experiment with Token Limits**: Adjust token parameters to control response length
5. **Test Conversation Flow**: Use conversation history to test multi-turn interactions

## Common Issues

### Invalid conversation_history format
❌ **Wrong:**
```json
{
  "conversation_history": [
    {
      "additionalProp1": {}
    }
  ]
}
```

✅ **Correct:**
```json
{
  "conversation_history": [
    {
      "role": "user",
      "content": "What is the main topic?"
    },
    {
      "role": "assistant", 
      "content": "The main topic is..."
    }
  ]
}
```

### Invalid mode values
Only use: `"local"`, `"global"`, `"hybrid"`, `"naive"`, `"mix"`, `"bypass"`

### Token limits
All token parameters must be greater than 1: `max_token_for_text_unit`, `max_token_for_global_context`, `max_token_for_local_context`

## Testing Workflow

1. **Upload Documents**: First upload some PDFs using the document pipeline endpoints
2. **Test Basic Query**: Start with a simple query to verify the system works
3. **Test Context Retrieval**: Use `only_need_context: true` to see what context is retrieved
4. **Test Response Generation**: Use `only_need_prompt: false` to get full responses
5. **Test Streaming**: Use the `/rag/query/stream` endpoint for real-time responses
6. **Test Conversation**: Build up conversation history to test multi-turn interactions 
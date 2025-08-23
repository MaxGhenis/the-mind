# Response to John's Comment on n Parameter Issue

Hi John,

Great question about which providers support this! I did comprehensive testing, and here's what I found:

## Provider Support for Multiple Completions

| Provider | Parameter | **Max Limit** | API Documentation |
|----------|-----------|---------------|-------------------|
| **OpenAI** | `n` | **128** | [API Reference](https://platform.openai.com/docs/api-reference/chat/create#chat-create-n): `n: integer, Optional, Defaults to 1. How many chat completion choices to generate for each input message. Note that you will be charged based on the number of generated tokens across all of the choices.` |
| **Azure OpenAI** | `n` | **128** | Same as OpenAI - [Azure Reference](https://learn.microsoft.com/en-us/azure/ai-services/openai/reference#completions) |
| **Google Gemini** | `candidateCount` | **8** | [API Reference](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/inference#generationconfig): `candidateCount: integer, Optional. The number of response variations to return. For each request, you're charged for the output tokens of all candidates, but are only charged once for the input tokens.` Range: 1-8 for Gemini 2.0+ |
| **Anthropic** | - | None | [API Reference](https://docs.anthropic.com/en/api/messages): No `n` parameter. The Messages API only returns a single response per request. |
| **Together AI** | - | None | [API Reference](https://docs.together.ai/reference/completions): No `n` parameter documented in their completions endpoint. |
| **Groq** | `n` | 1 only | [API Reference](https://console.groq.com/docs/api-reference#chat-create): `n: integer or null, Optional, default: 1. Note that at the current moment, only n=1 is supported.` |
| **Mistral** | - | None | [API Reference](https://docs.mistral.ai/api#operation/createChatCompletion): No `n` parameter in chat completions. |
| **Others** | - | None | Bedrock ([ref](https://docs.aws.amazon.com/bedrock/latest/userguide/)), Replicate ([ref](https://replicate.com/docs)), Deep Infra - no `n` equivalent |

## Key Findings

1. **Only OpenAI and Google** truly support this cost-saving feature
2. **OpenAI is the clear winner** with n≤128 (16x more than Gemini's limit of 8)
3. **Cost savings are massive**: At n=100, it's 99% savings on input tokens with OpenAI

## Your Proposal

I think your approach makes perfect sense - intercepting `run(n=...)` to use native parameters when available. Here's how I'd implement it:

```python
def run(self, n=1, **kwargs):
    """Run survey/question with n iterations."""
    
    # Detect which model is being used
    model_service = self.model.service_name
    
    if model_service in ["openai", "azure"]:
        # Use native n parameter (up to 128)
        if n <= 128:
            # Single API call with n parameter
            return self._run_with_param(n=n, **kwargs)
        else:
            # Batch into chunks of 128
            results = []
            for i in range(0, n, 128):
                batch_size = min(128, n - i)
                results.extend(self._run_with_param(n=batch_size, **kwargs))
            return results
            
    elif model_service == "google":
        # Use candidateCount (up to 8)
        if n <= 8:
            return self._run_with_param(candidateCount=n, **kwargs)
        else:
            # Batch into chunks of 8
            results = []
            for i in range(0, n, 8):
                batch_size = min(8, n - i)
                results.extend(self._run_with_param(candidateCount=batch_size, **kwargs))
            return results
            
    else:
        # No support - fall back to current behavior (n separate calls)
        return [self._run_single(**kwargs) for _ in range(n)]
```

## Implementation Considerations

1. **Model detection**: We'd need to know which provider is being used (already in Model object)
2. **Parameter mapping**: Pass `n` for OpenAI/Azure, `candidateCount` for Google
3. **Batching logic**: For n>limit, intelligently batch requests
4. **Backward compatibility**: Default behavior for unsupported providers

## Why This Matters

For research requiring multiple samples (like our Mind game experiments):

- **Current approach**: 100 samples = 100 API calls = 100x input tokens
- **With your proposal**: 100 samples = 1 API call = 1x input tokens (99% savings!)

The issue (#2185) and this PR for parameter validation (#2186) are first steps. Should we open a separate issue for implementing the n parameter properly?

Let me know your thoughts!

---

*Note: All limits were empirically tested. OpenAI returns error "Expected a value <= 128" for n=129, and Gemini returns "must be in range [1, 8]" for candidateCount=9.*
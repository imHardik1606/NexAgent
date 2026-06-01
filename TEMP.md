I want to add observability to my project using TraceRoot.

My project uses [Python / TypeScript/Node.js] — adjust the instructions to match my stack.

**Python setup:**
1. Install: pip install traceroot
2. Initialize at the entry point, before any LLM imports:
   from dotenv import load_dotenv
   load_dotenv()
   import traceroot
   from traceroot import Integration
   traceroot.initialize(integrations=[
       Integration.OPENAI,        # if using OpenAI
       Integration.LANGCHAIN,     # if using LangChain/LangGraph/DeepAgents
       Integration.ANTHROPIC,     # if using Anthropic
       Integration.GOOGLE_GENAI,  # if using Google Gemini
       Integration.MISTRAL,       # if using Mistral
       Integration.CREWAI,        # if using CrewAI
       Integration.AUTOGEN,       # if using AutoGen (AG2)
       Integration.LLAMA_INDEX,   # if using LlamaIndex
       Integration.AGNO,          # if using Agno
       Integration.DSPY,          # if using DSPy
       Integration.GOOGLE_ADK,    # if using Google ADK
   ])
3. Add @observe on agent entrypoints and tool functions:
   from traceroot import observe
   @observe(name="my_agent", type="agent")
   def run(query): ...
4. Wrap request handlers with using_attributes to attach user/session context:
   from traceroot import using_attributes
   with using_attributes(user_id="u-123", session_id="s-456"):
       result = run(query)
5. Call traceroot.flush() at the end of short-lived scripts.

**TypeScript/Node.js setup:**
1. Install: npm install @traceroot-ai/traceroot
2. Initialize at the entry point, before any LLM imports:
   import { TraceRoot } from '@traceroot-ai/traceroot';
   import OpenAI from 'openai';
   import Anthropic from '@anthropic-ai/sdk';
   import * as lcCallbackManager from '@langchain/core/callbacks/manager';
   TraceRoot.initialize({
     instrumentModules: {
       openAI: OpenAI,                    // if using OpenAI
       anthropic: Anthropic,              // if using Anthropic
       langchain: lcCallbackManager,      // if using LangChain/LangGraph/DeepAgents
     },
   });

   For Mastra, use the dedicated exporter instead:
   npm install @traceroot-ai/mastra
   import { TraceRootExporter } from '@traceroot-ai/mastra';
   const exporter = new TraceRootExporter({ apiKey: process.env.TRACEROOT_API_KEY });
   // Pass exporter to Mastra's Observability config (see docs/integrations/mastra)

   For the Vercel AI SDK, no instrumentModules entry is needed:
   TraceRoot.initialize();
   // Then on each generateText / streamText / generateObject call, set:
   //   experimental_telemetry: { isEnabled: true }
   // (See docs/integrations/vercel-ai)
3. Wrap agent entrypoints and tool functions with observe():
   import { observe } from '@traceroot-ai/traceroot';
   const result = await observe({ name: 'my_agent', type: 'agent' }, async () => {
     return await runPipeline(query);
   });
4. Wrap request handlers with usingAttributes to attach user/session context:
   import { usingAttributes } from '@traceroot-ai/traceroot';
   const result = await usingAttributes(
     { userId: 'u-123', sessionId: 's-456' },
     async () => await runAgent(query),
   );
5. Call await TraceRoot.flush() at the end of short-lived scripts.

The TRACEROOT_API_KEY environment variable is already set in my .env file.
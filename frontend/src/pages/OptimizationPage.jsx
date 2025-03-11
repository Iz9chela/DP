import React, { useState } from 'react';
import { createOptimizedPrompt } from '../api/optimizationApi';
import { InputText } from 'primereact/inputtext';
import { Dropdown } from 'primereact/dropdown';
import { InputNumber } from 'primereact/inputnumber';
import { Button } from 'primereact/button';

function OptimizationPage() {
  // -- Provider & model dynamic mapping --
  const providerOptions = [
    { label: 'OpenAI', value: 'openai' },
    { label: 'Claude', value: 'claude' }
  ];

  const modelOptionsMap = {
    openai: [
      { label: 'gpt-3.5-turbo', value: 'gpt-3.5-turbo' },
      { label: 'gpt-4o', value: 'gpt-4o' },
      { label: 'gpt-4o-mini', value: 'gpt-4o-mini' }
    ],
    claude: [
      { label: 'claude-3-haiku-20240307', value: 'claude-3-haiku-20240307' },
      { label: 'claude-3-5-haiku-latest', value: 'claude-3-5-haiku-latest' },
      { label: 'claude-3-7-sonnet-latest', value: 'claude-3-7-sonnet-latest' }
    ]
  };

  // -- Technique options --
  const techniqueOptions = [
    { label: 'Chain of Thought (CoT)', value: 'CoT' },
    { label: 'Self-Consistency (SC)', value: 'SC' },
    { label: 'CoD', value: 'CoD' },
    { label: 'Prompt Chaining (PC)', value: 'PC' },
    { label: 'ReAct', value: 'ReAct' },
    { label: 'SC + ReAct', value: 'SC_ReAct' }
  ];

  // -- React state for form fields --
  const [userQuery, setUserQuery] = useState('');
  const [provider, setProvider] = useState('openai');
  const [model, setModel] = useState(modelOptionsMap['openai'][0].value);
  const [technique, setTechnique] = useState('CoT');
  const [iterations, setIterations] = useState(3);

  // -- State to store results after optimization --
  const [result, setResult] = useState(null);

  // Handle provider changes, update model list accordingly
  function handleProviderChange(e) {
    setProvider(e.value);
    setModel(modelOptionsMap[e.value][0].value); // reset model to first
  }

  async function handleOptimize() {
    try {
      const promptData = {
        user_query: userQuery,
        provider,
        model,
        technique,
        number_of_iterations: iterations
      };
      // Call the optimization API function
      const responseData = await createOptimizedPrompt(promptData);
      setResult(responseData); // store entire response
    } catch (error) {
      console.error(error);
      alert(error.message);
    }
  }

  return (
    <div className="p-4">
      <h2>Optimization Page</h2>

      <div className="field mb-3">
        <label htmlFor="userQuery" className="block mb-2">User Query</label>
        <InputText
          id="userQuery"
          value={userQuery}
          onChange={(e) => setUserQuery(e.target.value)}
          placeholder="Enter text to optimize..."
          className="w-full"
        />
      </div>

      <div className="field mb-3">
        <label className="block mb-2">Provider</label>
        <Dropdown
          value={provider}
          options={providerOptions}
          onChange={handleProviderChange}
          placeholder="Select Provider"
          className="w-full"
        />
      </div>

      <div className="field mb-3">
        <label className="block mb-2">Model</label>
        <Dropdown
          value={model}
          options={modelOptionsMap[provider]} // show models relevant to selected provider
          onChange={(e) => setModel(e.value)}
          placeholder="Select Model"
          className="w-full"
        />
      </div>

      <div className="field mb-3">
        <label className="block mb-2">Technique</label>
        <Dropdown
          value={technique}
          options={techniqueOptions}
          onChange={(e) => setTechnique(e.value)}
          placeholder="Select Technique"
          className="w-full"
        />
      </div>

      <div className="field mb-3">
        <label htmlFor="iterations" className="block mb-2">Number of Iterations</label>
        <InputNumber
          id="iterations"
          value={iterations}
          onValueChange={(e) => setIterations(e.value)}
          min={3}
        />
      </div>

      <Button label="Optimize" onClick={handleOptimize} className="mt-2" />

      {/* Display result if available */}
      {result && (
        <div className="mt-4 p-3 border-1 border-round surface-border">
          <h3>Final Optimized Query:</h3>
          <pre>{result.final_optimized_query}</pre>

          <h4>Raw Optimization Output:</h4>
          <pre>{JSON.stringify(result.optimized_output, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default OptimizationPage;

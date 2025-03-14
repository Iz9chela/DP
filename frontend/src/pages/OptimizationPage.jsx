import React, { useState, useEffect } from 'react';
import { createOptimizedPrompt, updateOptimizedPrompt } from '../api/optimizationApi';
import { InputTextarea } from 'primereact/inputtextarea';
import { Dropdown } from 'primereact/dropdown';
import { InputNumber } from 'primereact/inputnumber';
import { useNavigate } from 'react-router-dom';
import { InputSwitch } from 'primereact/inputswitch';
import { Button } from 'primereact/button';

// Helper to copy text to clipboard
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).catch(err => {
    console.error('Failed to copy:', err);
  });
}

function OptimizationPage() {
  // -- Greeting with full name from localStorage
  const [fullName, setFullName] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const storedName = localStorage.getItem('fullName');
    if (storedName) {
      setFullName(storedName);
    }
  }, []);

  // We set the switch to false => "Optimization" is active by default
  const [evaluationMode, setEvaluationMode] = useState(false);

  function handleToggle(e) {
    const newValue = e.value;  // boolean
    setEvaluationMode(newValue);
    if (newValue) {
      // If turned ON => navigate to evaluation
      navigate('/evaluate');
    }
  }

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

  // -- Store the entire creation/optimization response
  const [rawResponse, setRawResponse] = useState(null);
  const [optimizedOutput, setOptimizedOutput] = useState('');
  const [result, setResult] = useState(null);

  // -- Track if the user has applied Expert/Emotional once
  const [expertAdded, setExpertAdded] = useState(false);
  const [emotionalAdded, setEmotionalAdded] = useState(false);

  const [alternateQueries, setAlternateQueries] = useState([]);
  const [showOtherResults, setShowOtherResults] = useState(false);

  // Handle provider changes
  function handleProviderChange(e) {
    setProvider(e.value);
    setModel(modelOptionsMap[e.value][0].value);
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
      const responseData = await createOptimizedPrompt(promptData);

      console.log('Response =>', responseData);

      setResult(responseData);
      setRawResponse(responseData.raw_output);

      let tempOptimized = '';
      const fromRaw = responseData.raw_output?.final_optimized_query;
      if (typeof fromRaw === 'string' && fromRaw.length > 0) {
        tempOptimized = fromRaw;
      } else {
        tempOptimized = responseData.final_optimized_query || '';
      }
      setOptimizedOutput(tempOptimized);

      localStorage.setItem('optimizedPromptId', responseData._id);
      localStorage.setItem('expertPersona', responseData.expert_persona_text || '');
      localStorage.setItem('emotionalStimulus', responseData.emotional_stimuli_text || '');

      setExpertAdded(false);
      setEmotionalAdded(false);

      // TODO THIS IS OPTIONAL
      
      let altQ = [];
      if (technique === 'SC' || technique === 'SC_ReAct') {
        // raw_output.Interpretations => each item has "Optimized_Query"
        if (Array.isArray(rawResponse.Interpretations)) {
          altQ = rawResponse.Interpretations.map((interp) => interp.Optimized_Query).filter(Boolean);
        }
      } else if (technique === 'CoD') {
        // raw_output.All_Densities => each item has "Optimized_Query"
        if (Array.isArray(rawResponse.All_Densities)) {
          altQ = rawResponse.All_Densities.map((dens) => dens.Optimized_Query).filter(Boolean);
        }
      }

      // For other techniques (CoT, PC, ReAct), presumably no multi-Optimized_Query
      setAlternateQueries(altQ);
      setShowOtherResults(false);

    } catch (error) {
      console.error(error);
      alert(error.message);
    }
  }

  function handleCopy() {
    if (optimizedOutput) {
      copyToClipboard(optimizedOutput);
      alert('Copied to clipboard!');
    }
  }

  function handleDownload() {
    if (!result) return;
    const dataStr = JSON.stringify(rawResponse, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = 'optimized_prompt.json';
    link.click();

    URL.revokeObjectURL(url);
  }

  // Add expert persona -> calls PUT to update final_optimized_query
  async function handleAddExpert() {
    try {
      if (!result?._id) {
        throw new Error('No optimized prompt found or missing ID.');
      }

      if (expertAdded) return;

      // Prepend the expertPersona text
      const expertPersona = localStorage.getItem('expertPersona') || '';
      const newOutput = `${expertPersona}\n${optimizedOutput}`;
      setOptimizedOutput(newOutput);
      setExpertAdded(true);

      await updateOptimizedPrompt(result._id, {
        final_optimized_query: newOutput
      });

    } catch (error) {
      console.error(error);
      alert(error.message);
    }
  }

  // Add emotional stimulus -> calls PUT to update final_optimized_query
  async function handleAddEmotionalStimulus() {
    try {
      if (!result?._id) {
        throw new Error('No optimized prompt found or missing ID.');
      }

      if (emotionalAdded) return; // Only 1 time

       // Append the emotionalStimulus text
      const emotionalStimulus = localStorage.getItem('emotionalStimulus') || '';
      const newOutput = `${optimizedOutput}\n${emotionalStimulus}`;
      setOptimizedOutput(newOutput);
      setEmotionalAdded(true);

      await updateOptimizedPrompt(result._id, {
        final_optimized_query: newOutput
      });

    } catch (error) {
      console.error(error);
      alert(error.message);
    }
  }

  function handleViewOtherResults() {
    // If user wants to see them, set showOtherResults = true, hide after 5s
    setShowOtherResults(true);
    setTimeout(() => {
      setShowOtherResults(false);
    }, 5000);
  }

  const hasResultId = Boolean(result?._id);
  const hasOptimized = optimizedOutput.trim().length > 0;
  const canDownload = rawResponse !== null;
  const showAlternateButton =
  (technique === 'SC' || technique === 'SC_ReAct' || technique === 'CoD') &&
  alternateQueries.length > 0;

  return (
    <div className="p-4">
      {/* Greeting in top-right */}
      <div className="flex justify-content-end" style={{ marginBottom: '1rem' }}>
        <span>Hello, {fullName}</span>
      </div>

      <h2>Optimization Page</h2>

      {/* Larger input area for user query */}
      <div className="field mb-3">
        <label
          htmlFor="userQuery"
          className="block mb-2"
          style={{ fontSize: '1.5rem', fontWeight: 'bold' }}
        >
          User Query
        </label>
        <InputTextarea
          id="userQuery"
          value={userQuery}
          onChange={(e) => setUserQuery(e.target.value)}
          placeholder="Enter text to optimize..."
          className="w-full"
          rows={8}  // Make it tall
          cols={50} // Make it wider if needed
        />
      </div>

      <div className="flex align-items-center" style={{ marginTop: '1rem' }}>
        <span style={{ marginRight: '0.5rem' }}>Optimization</span>
        <InputSwitch checked={evaluationMode} onChange={handleToggle} />
        <span style={{ marginLeft: '0.5rem' }}>Evaluation</span>
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
          options={modelOptionsMap[provider]}
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
        <label htmlFor="iterations" className="block mb-2">
          Number of Iterations
        </label>
        <InputNumber
          id="iterations"
          value={iterations}
          onValueChange={(e) => setIterations(e.value)}
          min={1}
        />
      </div>

      <Button label="Optimize" onClick={handleOptimize} className="mt-2" />

      {/* After we get a response */}
      {result && (
        <div className="mt-4 p-3 border-1 border-round surface-border">
          <div className="flex align-items-center justify-content-between">
            <h3>Final Optimized Query:</h3>
            <div>
              {/* Copy icon */}
              <Button
                icon="pi pi-copy"
                className="p-button-text p-button-rounded mr-2"
                onClick={handleCopy}
                tooltip="Copy"
                disabled={!optimizedOutput}
              />
              {/* Download icon (downloads rawResponse) */}
              <Button
                icon="pi pi-download"
                className="p-button-rounded p-button-text"
                onClick={handleDownload}
                tooltip="Check model's thoughts"
                disabled={!canDownload}
              />
            </div>
          </div>

          {/* Larger output area to display final_optimized_query */}
          <InputTextarea
            value={optimizedOutput}
            rows={8}
            cols={50}
            readOnly
            className="w-full mt-2"
          />

          {/* Buttons for adding expert or emotional stimulus */}
          <div className="flex gap-2 mt-3">
            <Button
              label="Add Expert Persona"
              onClick={handleAddExpert}
              disabled={!hasResultId || expertAdded || !hasOptimized}
              className="p-button-primary"
            />
            <Button
              label="Add Emotional Stimulus"
              onClick={handleAddEmotionalStimulus}
              disabled={!hasResultId || emotionalAdded || !hasOptimized}
              className="p-button-warning"
            />
          </div>

         {/* -------------- "View other results" -------------- */}
         {showAlternateButton && (
            <Button
              label="View other results"
              onClick={handleViewOtherResults}
              className="p-button-secondary mt-3"
            />
          )}

           {/* If user clicks => show for 5 seconds */}
          {showOtherResults && (
            <div className="mt-2 p-2 border-round" style={{ backgroundColor: '#f0f0f0' }}>
              <h4>Other Optimized Queries:</h4>
              {alternateQueries.map((item, idx) => (
                <p key={idx}>
                  {idx + 1}. {item}
                </p>
              ))}
              <small>These results will hide after 5 seconds...</small>
            </div>
          )}

        </div>
      )}
    </div>
  );
}


export default OptimizationPage;

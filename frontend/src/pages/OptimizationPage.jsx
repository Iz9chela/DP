import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { createOptimizedPrompt, updateOptimizedPrompt } from '../api/optimizationApi';
import { InputTextarea } from 'primereact/inputtextarea';
import { Dropdown } from 'primereact/dropdown';
import { InputNumber } from 'primereact/inputnumber';
import { useNavigate } from 'react-router-dom';
import { Button } from 'primereact/button';
import './all_page.css';
import 'primeicons/primeicons.css';
import { NavLink } from 'react-router-dom';
import { ProgressSpinner } from 'primereact/progressspinner';

// EvaluationResult component defined in the same file
function EvaluationResult({
  optimizedOutput,
  rating,
  reasons,
  canDownload,
  showAlternateButton,
  alternateQueries,
  handleCopy,
  handleDownload,
  handleAddExpert,
  handleAddEmotionalStimulus,
  handleViewOtherResults,
  hasResultId,
  expertAdded,
  emotionalAdded,
  hasOptimized,
}) {
  return (
    <div className="final-wrapper">
    <div className="mt-4 p-3 border-1 border-round surface-border">
      <div className="flex align-items-center justify-content-between">
        <h2>Final Optimized Query:</h2>
        <div>
          <Button
            icon="pi pi-copy"
            className="p-button-text p-button-rounded mr-2 button_size"
            onClick={handleCopy}
            tooltip="Copy"
            disabled={!optimizedOutput}
          />
          <Button
            icon="pi pi-download"
            className="p-button-rounded p-button-text button_size"
            onClick={handleDownload}
            tooltip="Check model's thoughts"
            disabled={!canDownload}
          />
        </div>
      </div>
      <InputTextarea
        value={optimizedOutput}
        rows={8}
        cols={50}
        readOnly
        className="w-full mt-2" style={{ width: '430px' }}
      />
      <div className="flex gap-2 mt-3">
        <Button
          label="Add Expert Persona"
          onClick={handleAddExpert}
          disabled={!hasResultId || expertAdded || !hasOptimized}
          className="p-button-primary execute_pos"
        />
        <Button
          label="Add Emotional Stimulus"
          onClick={handleAddEmotionalStimulus}
          disabled={!hasResultId || emotionalAdded || !hasOptimized}
          className="p-button-warning execute_pos"
        />
      </div>
      {showAlternateButton && (
        <Button
          label="View other results"
          onClick={handleViewOtherResults}
          className="p-button-secondary mt-3"
        />
      )}
      {alternateQueries && alternateQueries.length > 0 && (
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
    </div>
  );
}

EvaluationResult.propTypes = {
  optimizedOutput: PropTypes.string,
  rating: PropTypes.any,
  reasons: PropTypes.string,
  canDownload: PropTypes.bool,
  showAlternateButton: PropTypes.bool,
  alternateQueries: PropTypes.array,
  handleCopy: PropTypes.func,
  handleDownload: PropTypes.func,
  handleAddExpert: PropTypes.func,
  handleAddEmotionalStimulus: PropTypes.func,
  handleViewOtherResults: PropTypes.func,
  hasResultId: PropTypes.bool,
  expertAdded: PropTypes.bool,
  emotionalAdded: PropTypes.bool,
  hasOptimized: PropTypes.bool,
};

function OptimizationPage() {
  // Greeting with full name from localStorage
  const [fullName, setFullName] = useState('');
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);


  const [isProviderOpen, setIsProviderOpen] = useState(false);
  const [isModelOpen, setIsModelOpen] = useState(false);
  const [isEvalMethodOpen, setIsEvalMethodOpen] = useState(false);

  // *** Declare rating and reasons so they are available ***
  const [rating, setRating] = useState(null);
  const [reasons, setReasons] = useState('');

  const [alternateQueries, setAlternateQueries] = useState([]);
  const [showOtherResults, setShowOtherResults] = useState(false);

  const [userQuery, setUserQuery] = useState('');
  const [provider, setProvider] = useState('openai');
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
  const [model, setModel] = useState(modelOptionsMap['openai'][0].value);
  const [technique, setTechnique] = useState('CoT');
  const [iterations, setIterations] = useState(3);

  const [rawResponse, setRawResponse] = useState(null);
  const [optimizedOutput, setOptimizedOutput] = useState('');
  const [result, setResult] = useState(null);

  const [expertAdded, setExpertAdded] = useState(false);
  const [emotionalAdded, setEmotionalAdded] = useState(false);

  // For testing purposes, you can add dummy data here
  useEffect(() => {
    const storedName = localStorage.getItem('fullName');
    if (storedName) {
      setFullName(storedName);
    }
    // Uncomment these lines for testing dummy data:
    // setResult({ dummy: true });
    // setOptimizedOutput("This is a test optimized query output.");
    // setRating(8);
    // setReasons("Test reasons for the optimized query.");
  }, []);

  // -- Provider & model dynamic mapping --
  const providerOptions = [
    { label: 'OpenAI', value: 'openai' },
    { label: 'Claude', value: 'claude' }
  ];

  const techniqueOptions = [
    { label: 'Chain of Thought (CoT)', value: 'CoT' },
    { label: 'Self-Consistency (SC)', value: 'SC' },
    { label: 'CoD', value: 'CoD' },
    { label: 'Prompt Chaining (PC)', value: 'PC' },
    { label: 'ReAct', value: 'ReAct' },
    { label: 'SC + ReAct', value: 'SC_ReAct' }
  ];

  function handleProviderChange(e) {
    setProvider(e.value);
    setModel(modelOptionsMap[e.value][0].value);
  }
  const [errorMsg, setErrorMsg] = useState('');
  const [errornumberMsg, setErrornumberMsg] = useState('');
  async function handleOptimize() {
    setErrorMsg('');
    setErrornumberMsg('')
 
    if (!userQuery.trim()) {
      setErrorMsg('Please enter (or load) some text.');
      return;
    }

    if (iterations >5 || iterations < 3) {
      setErrornumberMsg('Please set the number from 3 to 5')
      return;
    }
    try {
      setIsLoading(true); // Set loading to true
      const promptData = {
        user_query: userQuery,
        provider,
        model,
        technique,
        number_of_iterations: iterations,
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
  
      let altQ = [];
      if (technique === 'SC' || technique === 'SC_ReAct') {
        if (rawResponse && Array.isArray(rawResponse.Interpretations)) {
          altQ = rawResponse.Interpretations.map((interp) => interp.Optimized_Query).filter(Boolean);
        }
      } else if (technique === 'CoD') {
        if (rawResponse && Array.isArray(rawResponse.All_Densities)) {
          altQ = rawResponse.All_Densities.map((dens) => dens.Optimized_Query).filter(Boolean);
        }
      }
      setAlternateQueries(altQ);
      setShowOtherResults(false);
    } catch (error) {
      console.error(error);
      alert(error.message);
    } finally {
      setIsLoading(false); // Always revert to false when done
    }
  }

  function handleCopy() {
    if (optimizedOutput) {
      navigator.clipboard.writeText(optimizedOutput).catch((err) => {
        console.error('Failed to copy:', err);
      });
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

  async function handleAddExpert() {
    try {
      if (!result?._id) {
        throw new Error('No optimized prompt found or missing ID.');
      }
      if (expertAdded) return;
      const expertPersona = localStorage.getItem('expertPersona') || '';
      const newOutput = `${expertPersona}\n${optimizedOutput}`;
      setOptimizedOutput(newOutput);
      setExpertAdded(true);
      await updateOptimizedPrompt(result._id, {
        final_optimized_query: newOutput,
      });
    } catch (error) {
      console.error(error);
      alert(error.message);
    }
  }

  async function handleAddEmotionalStimulus() {
    try {
      if (!result?._id) {
        throw new Error('No optimized prompt found or missing ID.');
      }
      if (emotionalAdded) return;
      const emotionalStimulus = localStorage.getItem('emotionalStimulus') || '';
      const newOutput = `${optimizedOutput}\n${emotionalStimulus}`;
      setOptimizedOutput(newOutput);
      setEmotionalAdded(true);
      await updateOptimizedPrompt(result._id, {
        final_optimized_query: newOutput,
      });
    } catch (error) {
      console.error(error);
      alert(error.message);
    }
  }

  function handleViewOtherResults() {
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
      <div className="columns-wrapper">
        <div className="form-container container_border">
          <div className="field mb-3" style={{ marginBottom: isProviderOpen ? '60px' : '30px' }}>
            <label className="block mb-2">AIclient:</label>
            <Dropdown
              value={provider}
              options={providerOptions}
              onChange={handleProviderChange}
              placeholder="Select Provider"
              className="w-full"
              appendTo="self"
              onShow={() => setIsProviderOpen(true)}
              onHide={() => setIsProviderOpen(false)}
            />
          </div>

          <div className="field mb-3" style={{ marginBottom: isModelOpen ? '80px' : '30px' }}>
            <label className="block mb-2">Model:</label>
            <Dropdown
              value={model}
              options={modelOptionsMap[provider]}
              onChange={(e) => setModel(e.value)}
              placeholder="Select Model"
              className="w-full"
              appendTo="self"
              onShow={() => setIsModelOpen(true)}
              onHide={() => setIsModelOpen(false)}
            />
          </div>

          <div className="field mb-3" style={{ marginBottom: isEvalMethodOpen ? '150px' : '30px' }}>
            <label className="block mb-2">Technique:</label>
            <Dropdown
              value={technique}
              options={techniqueOptions}
              onChange={(e) => setTechnique(e.value)}
              placeholder="Select Technique"
              className="w-full"
              appendTo="self"
              onShow={() => setIsEvalMethodOpen(true)}
              onHide={() => setIsEvalMethodOpen(false)}
            />
          </div>

          <div className="field mb-3">
            <label htmlFor="iterations" className="block mb-2">
              Number of Iterations:
            </label>
            <InputNumber
              id="iterations"
              value={iterations}
              onValueChange={(e) => setIterations(e.value)}
              min={1}
              className="custom-input-number"
              style={{ width: '20px' }}
            />
          </div>
          <div className="flex justify-content-end login" style={{ marginBottom: '1rem' }}>
            <span>Hello, {fullName}</span>
          </div>
        </div>
        
        <div className="user-query">
        <div className="menu">
          <li>
            <NavLink
              to="/evaluate"
              className={({ isActive }) => (isActive ? "grey active" : "grey")}
            >
              Evaluation Page
            </NavLink>
          </li>
          <li>
            <NavLink
              to="/compare"
              className={({ isActive }) => (isActive ? "grey active" : "grey")}
            >
              Compare Page
            </NavLink>
          </li>

          <li>
            <NavLink
              to="/blind"
              className={({ isActive }) => (isActive ? "grey active" : "grey")}
            >
              Leader Board Page
            </NavLink>
          </li>
        </div>
          <h2>Optimization Page</h2>
          <h2>Enter your query</h2>
          {errorMsg && (
        <div className="my-2 p-error" style={{ color: 'red' }}>
          {errorMsg}
        </div>
      )}
          {errornumberMsg && (
        <div className="my-2 p-error" style={{ color: 'red' }}>
          {errornumberMsg}
        </div>
        )}

          <div className="userContainer">
            <div className="field__center field__block mb-3">
              <InputTextarea
                id="userQuery"
                value={userQuery}
                onChange={(e) => setUserQuery(e.target.value)}
                placeholder="Enter text to optimize..."
                className="w-full"
                rows={4}
                cols={60}
              />
            </div>
              <Button  
              onClick={handleOptimize} 
              className="mt-2 execute_pos" 
              style={{ marginLeft: '150px' }} 
              >
              {isLoading ? (
                <span style={{ display: 'flex', alignItems: 'center' }}>
                  <ProgressSpinner style={{width: '20px', height: '20px'}} strokeWidth="4" fill="var(--surface-ground)" animationDuration=".5s" />
                  <span style={{ marginLeft: '0.5rem' }}>Optimizing...</span>
                </span>
              ) : (
                "Optimize"
              )}
              </Button>
            </div>
          {/* Always show EvaluationResult */}
          <EvaluationResult
            optimizedOutput={optimizedOutput}
            rating={rating}
            reasons={reasons}
            canDownload={canDownload}
            showAlternateButton={showAlternateButton}
            alternateQueries={alternateQueries}
            handleCopy={handleCopy}
            handleDownload={handleDownload}
            handleAddExpert={handleAddExpert}
            handleAddEmotionalStimulus={handleAddEmotionalStimulus}
            handleViewOtherResults={handleViewOtherResults}
            hasResultId={hasResultId}
            expertAdded={expertAdded}
            emotionalAdded={emotionalAdded}
            hasOptimized={hasOptimized}
          />
        </div>
      </div>
    </div>
  );
}

export default OptimizationPage;


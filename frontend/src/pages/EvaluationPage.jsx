import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { Dropdown } from 'primereact/dropdown';
import { InputTextarea } from 'primereact/inputtextarea';
import { Button } from 'primereact/button';
import { NavLink } from 'react-router-dom';
import { createEvaluation } from '../api/evaluationApi';
import { ProgressSpinner } from 'primereact/progressspinner';

function EvaluationPage() {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // Separate states for each dropdown's open status
  const [isProviderOpen, setIsProviderOpen] = useState(false);
  const [isModelOpen, setIsModelOpen] = useState(false);
  const [isEvalMethodOpen, setIsEvalMethodOpen] = useState(false);

  useEffect(() => {
    const storedName = localStorage.getItem('fullName');
    if (storedName) {
      setFullName(storedName);
    }
  }, []);

  const [evaluationMode, setEvaluationMode] = useState(true);
  function handleToggle(e) {
    const newVal = e.value; // boolean
    setEvaluationMode(newVal);
    if (!newVal) {
      navigate('/optimize');
    }
  }

  // States for user input
  const [userQuery, setUserQuery] = useState('');
  const [provider, setProvider] = useState('openai');
  const [model, setModel] = useState('gpt-3.5-turbo');
  const [evaluationMethod, setEvaluationMethod] = useState('human');

  const [rating, setRating] = useState(null);
  const [reasons, setReasons] = useState('');
  const [evaluationResult, setEvaluationResult] = useState(null);

  // Provider & Model dropdown data
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

  // Evaluate method options
  const evaluationMethodOptions = [
    { label: 'Human', value: 'human' },
    { label: 'LLM', value: 'llm' }
  ];

  // Handle provider change
  function handleProviderChange(e) {
    setProvider(e.value);
    setModel(modelOptionsMap[e.value][0].value);
  }
  const [errorMsg, setErrorMsg] = useState('');
  // On "Evaluate" button
  async function handleEvaluate() {
    setErrorMsg('');
 
    if (!userQuery.trim()) {
      setErrorMsg('Please enter (or load) some text.');
      return;
    }
    try {
      setIsLoading(true);
      const evaluationData = {
        user_query: userQuery,
        provider,
        model,
        evaluation_method: evaluationMethod,
      };
      const response = await createEvaluation(evaluationData);
      console.log('Evaluation result => ', response);

      setEvaluationResult(response);

      if (response.evaluation_result) {
        const aiRating = response.evaluation_result.prompt_rating;
        const aiReasons = response.evaluation_result.reasons;
        setRating(aiRating || null);
        setReasons(Array.isArray(aiReasons) ? aiReasons.join('\n') : aiReasons || '');
      } else {
        setRating(null);
        setReasons('');
      }
    } catch (err) {
      console.error(err);
      alert('Evaluation failed: ' + err.message);
    } finally {
      setIsLoading(false);
    }
    }


  return (
    <div className="p-4">
      <div className="columns-wrapper">
        {/* Left Column: Form Container */}
        <div className="form-container container_border">
          {/* Provider Dropdown */}
          <div className="field mb-3" style={{ marginBottom: isProviderOpen ? '60px' : '30px' }}>
            <label className="block mb-2">AIclient:</label>
            <Dropdown
              value={provider}
              options={providerOptions}
              onChange={handleProviderChange}
              className="w-full"
              appendTo="self"
              onShow={() => setIsProviderOpen(true)}
              onHide={() => setIsProviderOpen(false)}
            />
          </div>
          {/* Model Dropdown */}
          <div className="field mb-3" style={{ marginBottom: isModelOpen ? '80px' : '30px' }}>
            <label className="block mb-2">Model:</label>
            <Dropdown
              value={model}
              options={modelOptionsMap[provider]}
              onChange={(e) => setModel(e.value)}
              className="w-full"
              appendTo="self"
              onShow={() => setIsModelOpen(true)}
              onHide={() => setIsModelOpen(false)}
            />
          </div>

          {/* Evaluation Method Dropdown */}
          <div className="field mb-3">
            <label className="block mb-2">Evaluation Method:</label>
            <Dropdown
              value={evaluationMethod}
              options={evaluationMethodOptions}
              onChange={(e) => setEvaluationMethod(e.value)}
              className="w-full"
              appendTo="self"
            />
          </div>

          <div className="flex justify-content-end login" style={{ marginBottom: '1rem' }}>
            <span>Hello, {fullName}</span>
          </div>
        </div>
        
        {/* Right Column: User Query and Evaluation Result */}
        <div className="user-query">
        <div className="menu">
          <li>
            <NavLink
              to="/optimize"
              className={({ isActive }) => (isActive ? "grey active" : "grey")}
            >
              Optimization Page
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
          <h2>Evaluation Page</h2>
          
          {/* User Query */}
          <h2>Enter your query</h2>
          {errorMsg && (
        <div className="my-2 p-error" style={{ color: 'red' }}>
          {errorMsg}
        </div>
      )}
          <div className="field mb-3">
            <InputTextarea
              value={userQuery}
              onChange={(e) => setUserQuery(e.target.value)}
              rows={4}
              cols={60}
              placeholder="User Request..."
              className="w-full"
            />
          </div>
          <div className="field_btn">
            <Button  
            className="p-button-success mt-2 field__btn field__btn_left execute_pos" 
            onClick={handleEvaluate}
            >
            {isLoading ? (
              <span style={{ display: 'flex', alignItems: 'center' }}>
                <ProgressSpinner style={{width: '20px', height: '20px'}} strokeWidth="4" fill="var(--surface-ground)" animationDuration=".5s" />
                <span style={{ marginLeft: '0.5rem' }}>Evaluating...</span>
              </span>
            ) : (
              "Evaluate"
            )}
            </Button>

          </div>
          
          {/* Evaluation Result Block inside user-query */}
          { (
            <div className="mt-4 p-3 border-1 border-round surface-border">
              <h2>Evaluation Result</h2>
              <div className="evaluation_result">
              <InputTextarea
                     value={`Rating: ${rating}\nReasons: ${reasons}`}
                     rows={8}
                     cols={50}
                     readOnly
                     className="w-full mt-2" style={{ width: '430px' }}
            />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default EvaluationPage;

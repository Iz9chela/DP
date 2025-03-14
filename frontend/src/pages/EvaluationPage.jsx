import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { InputSwitch } from 'primereact/inputswitch';
import { Dropdown } from 'primereact/dropdown';
import { InputTextarea } from 'primereact/inputtextarea';
import { Button } from 'primereact/button';

import { createEvaluation } from '../api/evaluationApi';

function EvaluationPage() {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState('');

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
      // user toggled OFF => go to optimization
      navigate('/optimize');
    }
  }

  // 2. States for user input
  const [userQuery, setUserQuery] = useState('');
  const [provider, setProvider] = useState('openai');
  const [model, setModel] = useState('gpt-3.5-turbo');
  const [evaluationMethod, setEvaluationMethod] = useState('human');

  const [rating, setRating] = useState(null);
  const [reasons, setReasons] = useState('');

  const [evaluationResult, setEvaluationResult] = useState(null);

  // Provider & Model dropdown data (like your optimization page)
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

  // Evaluate method: "human" or "llm"
  const evaluationMethodOptions = [
    { label: 'Human', value: 'human' },
    { label: 'LLM', value: 'llm' }
  ];

  // 4. Handle provider changes => update model selection
  function handleProviderChange(e) {
    setProvider(e.value);
    setModel(modelOptionsMap[e.value][0].value);
  }

  // 5. On "Evaluate" button => call createEvaluation
  async function handleEvaluate() {
    try {
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
        const aiRating = response.evaluation_result.prompt_rating; // e.g., "8"
        const aiReasons = response.evaluation_result.reasons;      // array or string
        setRating(aiRating || null);
        setReasons(Array.isArray(aiReasons) ? aiReasons.join('\n') : aiReasons || '');
      } else {
        setRating(null);
        setReasons('');
      }
    } catch (err) {
      console.error(err);
      alert('Evaluation failed: ' + err.message);
    }
  }

  async function handleCompare() {
    navigate('/compare');
  }

  return (
    <div className="p-4">


      <div className="flex justify-content-end" style={{ marginBottom: '1rem' }}>
        <span>Hello, {fullName}</span>
      </div>

      {/* 1) Top toggle */}
      <div className="flex align-items-center mb-3">
        <span style={{ marginRight: '0.5rem' }}>Optimization</span>
        <InputSwitch checked={evaluationMode} onChange={handleToggle} />
        <span style={{ marginLeft: '0.5rem' }}>Evaluation</span>
      </div>

      <h2>Evaluation Page</h2>

      {/* 2) User Query */}
      <div className="field mb-3">
        <label className="block mb-2">Test Your Prompt</label>
        <InputTextarea
          value={userQuery}
          onChange={(e) => setUserQuery(e.target.value)}
          rows={4}
          cols={60}
          placeholder="User Request..."
          className="w-full"
        />
      </div>

      {/* 3) Provider */}
      <div className="field mb-3">
        <label className="block mb-2">Provider</label>
        <Dropdown
          value={provider}
          options={providerOptions}
          onChange={handleProviderChange}
          className="w-full"
        />
      </div>

      {/* 4) Model */}
      <div className="field mb-3">
        <label className="block mb-2">Model</label>
        <Dropdown
          value={model}
          options={modelOptionsMap[provider]}
          onChange={(e) => setModel(e.value)}
          className="w-full"
        />
      </div>

      {/* 5) Evaluation Method */}
      <div className="field mb-3">
        <label className="block mb-2">Evaluation Method</label>
        <Dropdown
          value={evaluationMethod}
          options={evaluationMethodOptions}
          onChange={(e) => setEvaluationMethod(e.value)}
          className="w-full"
        />
      </div>

       {/* Evaluate button */}
      <Button label="Evaluate" className="p-button-success mt-2" onClick={handleEvaluate} />

      <Button label="Compare" className="p-button-info mt-2" onClick={handleCompare}/>

      {/* Show rating & reasons after success */}
      {evaluationResult && (
        <div className="mt-4 p-3 border-1 border-round surface-border">
          <h4>Evaluation Result</h4>
          <p>Rating: {rating || 'N/A'}</p>
          <p>Reasons:</p>
          <pre>{reasons || 'No reasons given'}</pre>
        </div>
      )}
    </div>
  );
}

export default EvaluationPage;

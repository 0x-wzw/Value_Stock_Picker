import { useState } from 'react'

function App() {
    return (
        <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
            <h1 className="text-4xl font-bold text-blue-600 mb-4">Value Stock Picker</h1>
            <p className="text-gray-600 text-lg mb-8">
                Investigative workbench for deep fundamental analysis.
            </p>

            <div className="bg-white p-6 rounded-lg shadow-md max-w-sm w-full">
                <h2 className="text-xl font-semibold mb-4 text-gray-800">System Status</h2>
                <ul className="space-y-2 text-left">
                    <li className="flex items-center text-green-600">
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
                        Frontend Container Active
                    </li>
                    <li className="flex items-center text-amber-500">
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        Backend API Pending Connection
                    </li>
                </ul>
            </div>
        </div>
    )
}

export default App

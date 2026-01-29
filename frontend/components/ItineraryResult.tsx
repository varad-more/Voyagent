import { useState } from "react";
import { apiFetch } from "@/lib/api";
import { ItineraryResponse, ScheduleBlock, TravelOption } from "@/lib/types";
import { format } from "date-fns";

interface ItineraryResultProps {
  itinerary: ItineraryResponse;
  onReset: () => void;
}

export default function ItineraryResult({ itinerary, onReset }: ItineraryResultProps) {
  const formatTime = (timeStr: string) => {
    try {
      const [hours, minutes] = timeStr.split(":");
      const date = new Date();
      date.setHours(parseInt(hours), parseInt(minutes));
      return format(date, "h:mm a");
    } catch (e) {
      return timeStr;
    }
  };

  const getDayLabel = (dateStr: string) => {
    try {
      return format(new Date(dateStr), "EEEE, MMM do");
    } catch {
      return dateStr;
    }
  };

  /* State for local updates */
  const [currentItinerary, setCurrentItinerary] = useState(itinerary);
  const [editingBlock, setEditingBlock] = useState<{ dayIndex: number; blockIndex: number; block: ScheduleBlock } | null>(null);
  const [editInstruction, setEditInstruction] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [suggestedBlock, setSuggestedBlock] = useState<ScheduleBlock | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const handleEditClick = (dayIndex: number, blockIndex: number, block: ScheduleBlock) => {
    setEditingBlock({ dayIndex, blockIndex, block });
    setEditInstruction("");
    setSuggestedBlock(null);
  };

  const submitEdit = async () => {
    if (!editingBlock || !editInstruction) return;
    setIsEditing(true);
    try {
      const newBlock = await apiFetch<ScheduleBlock>("/api/edit/block", {
        method: "POST",
        body: JSON.stringify({
          day_index: editingBlock.dayIndex,
          block_index: editingBlock.blockIndex,
          instruction: editInstruction,
          current_block: editingBlock.block,
          destination: currentItinerary.summary.split("trip to ")[1]?.split(" ")[0] || "Unknown",
        }),
      });
      setSuggestedBlock(newBlock);
    } catch (err) {
      alert("Failed to generate suggestion. Try again.");
      console.error(err);
    } finally {
      setIsEditing(false);
    }
  };

  const handleSave = async () => {
    if (!suggestedBlock || !editingBlock) return;
    setIsSaving(true);
    try {
      const newDays = [...currentItinerary.days];
      const targetDay = { ...newDays[editingBlock.dayIndex] };
      const targetSchedule = [...targetDay.schedule];

      targetSchedule[editingBlock.blockIndex] = suggestedBlock;
      targetDay.schedule = targetSchedule;
      newDays[editingBlock.dayIndex] = targetDay;

      const updatedItinerary = { ...currentItinerary, days: newDays };

      await apiFetch(`/api/itineraries/${currentItinerary.itinerary_id}`, {
        method: 'PATCH',
        body: JSON.stringify(updatedItinerary)
      });

      setCurrentItinerary(updatedItinerary);
      setEditingBlock(null);
      setSuggestedBlock(null);
    } catch (err) {
      alert("Failed to save changes.");
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto space-y-12 animate-fadeIn">
      {/* Header Section */}
      <div className="text-center space-y-6 animate-scaleIn">
        <div className="inline-block relative">
          <div className="absolute inset-0 bg-blue-500 blur-3xl opacity-20 rounded-full"></div>
          <div className="relative text-6xl">✨</div>
        </div>
        <h2 className="text-4xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400">
          Your Adventure is Ready!
        </h2>

        <div className="glass-card p-8 rounded-2xl relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500"></div>
          <p className="text-xl text-slate-200 leading-relaxed font-light">
            {currentItinerary.summary}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Timeline (2/3 width) */}
        <div className="lg:col-span-2 space-y-10">
          <h3 className="text-2xl font-bold text-white flex items-center gap-3">
            <span className="text-3xl">📅</span> Day-by-Day Journey
          </h3>

          <div className="space-y-16">
            {currentItinerary.days.map((day, dayIndex) => (
              <div key={dayIndex} className="relative pl-8 border-l-2 border-slate-700 space-y-8">
                {/* Day Header */}
                <div className="absolute -left-2.5 top-0 w-5 h-5 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.5)]"></div>
                <div className="glass-card p-6 rounded-xl border border-white/10 bg-slate-800/40 backdrop-blur-md">
                  <h4 className="text-2xl font-bold text-white mb-2">{getDayLabel(day.date)}</h4>
                  <p className="text-purple-300 font-medium">{day.title}</p>
                  <div className="mt-4 flex items-center gap-2 text-sm text-slate-400 bg-slate-900/50 p-2 rounded-lg w-fit">
                    <span>🌦️</span> {day.weather_summary}
                  </div>
                </div>

                {/* Timeline Events */}
                <div className="space-y-6">
                  {day.schedule.map((block, i) => (
                    <div
                      key={i}
                      className="relative group transition-all duration-300 hover:translate-x-1"
                    >
                      {/* Timeline Connector Icon */}
                      <div className={`absolute -left-[42px] top-4 w-7 h-7 rounded-full flex items-center justify-center text-xs border-2 border-slate-900 shadow-lg z-10
                        ${block.block_type === 'travel' ? 'bg-slate-700 text-slate-300' :
                          block.block_type === 'meal' ? 'bg-emerald-600 text-white' :
                            'bg-indigo-600 text-white'
                        }`}>
                        {block.block_type === 'travel' ? '🚗' :
                          block.block_type === 'meal' ? '🍽️' : '🏔️'}
                      </div>

                      <div className={`rounded-xl p-5 border transition-all duration-300 relative
                          ${block.block_type === 'travel'
                          ? 'bg-slate-800/30 border-slate-700/50 border-dashed'
                          : 'glass-card border-white/5 hover:border-purple-500/30 bg-slate-800/60'
                        }
                      `}>
                        {/* Edit Button (Visible on Hover) */}
                        {block.block_type !== 'travel' && (
                          <button
                            onClick={() => handleEditClick(dayIndex, i, block)}
                            className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 p-2 bg-slate-700/80 hover:bg-purple-600 text-white rounded-lg transition-all shadow-lg"
                            title="Ask Gemini to edit this block"
                          >
                            ✏️
                          </button>
                        )}

                        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-1">
                              <span className={`text-sm font-mono px-2 py-0.5 rounded ${block.block_type === 'travel' ? 'bg-slate-700/50 text-slate-400' : 'bg-purple-900/30 text-purple-200'
                                }`}>
                                {formatTime(block.start_time)} - {formatTime(block.end_time)}
                              </span>
                            </div>
                            <h5 className="text-lg font-bold text-white mb-1 group-hover:text-purple-300 transition-colors">
                              {block.title}
                            </h5>
                            <p className="text-slate-400 text-sm leading-relaxed">{block.description}</p>

                            {block.micro_activities && block.micro_activities.length > 0 && (
                              <div className="mt-3 flex flex-wrap gap-2">
                                {block.micro_activities.map((act, idx) => (
                                  <span key={idx} className="text-xs px-2 py-1 rounded-full bg-slate-700/50 text-slate-300 border border-slate-600/50">
                                    • {typeof act === 'string' ? act : act.name}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Widgets (1/3 width) */}
        <div className="space-y-8">

          {/* Action Buttons */}
          <div className="flex flex-col gap-3 sticky top-4 z-20">
            <button
              onClick={() => alert("Calendar download feature coming soon!")}
              className="w-full py-4 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold shadow-lg shadow-purple-900/30 hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-2"
            >
              <span>📅</span> Add to Calendar
            </button>
            <button
              onClick={onReset}
              className="w-full py-3 rounded-xl bg-slate-800/80 text-slate-300 font-medium border border-slate-700 hover:bg-slate-700 transition-colors"
            >
              Start New Plan
            </button>
          </div>

          {/* Transport Analysis Widget */}
          {currentItinerary.transport_analysis && (
            <div className="glass-card p-6 rounded-2xl border border-white/10">
              <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <span>🚆</span> Transport Recommendations
              </h3>
              <div className="mb-4">
                <div className="text-sm text-slate-400 mb-1">Recommended Mode</div>
                <div className="text-lg font-bold text-emerald-400">{currentItinerary.transport_analysis.recommended_mode}</div>
                <p className="text-sm text-slate-300 mt-2 italic">"{currentItinerary.transport_analysis.reasoning}"</p>
              </div>
              <div className="space-y-3 pt-3 border-t border-slate-700/50">
                {currentItinerary.transport_analysis.options.map((opt, i) => (
                  <div key={i} className="p-3 bg-slate-800/50 rounded-lg border border-slate-700/30">
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-bold text-white capitalize">{opt.mode.replace('_', ' ')}</span>
                      <span className="text-xs bg-slate-700 px-1.5 py-0.5 rounded text-slate-300">{opt.cost_estimate}</span>
                    </div>
                    <p className="text-xs text-slate-400 mb-1">{opt.duration_estimate}</p>
                    <div className="flex flex-wrap gap-2 mb-1">
                      {opt.fuel_cost_estimate && <span className="text-[10px] bg-slate-700/50 px-1 rounded text-slate-400">⛽ {opt.fuel_cost_estimate}</span>}
                      {opt.misc_costs?.map((m, k) => <span key={k} className="text-[10px] bg-slate-700/50 px-1 rounded text-slate-400">🏷️ {m}</span>)}
                    </div>
                    <p className="text-xs text-slate-300">{opt.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Travel Options Widget */}
          {currentItinerary.travel_options && currentItinerary.travel_options.length > 0 && (
            <div className="glass-card p-6 rounded-2xl border border-white/10">
              <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <span>✈️</span> Travel & Booking
              </h3>
              <div className="space-y-4">
                {currentItinerary.travel_options.map((opt, idx) => (
                  <div key={idx} className="p-4 bg-slate-900/50 rounded-xl border border-slate-700/50 hover:border-blue-500/30 transition-all group">
                    <div className="flex justify-between items-start mb-2">
                      <span className={`text-xs px-2 py-1 rounded-full border ${opt.type === 'flight' ? 'bg-sky-900/30 text-sky-300 border-sky-500/30' :
                        opt.type === 'hotel' ? 'bg-purple-900/30 text-purple-300 border-purple-500/30' :
                          'bg-emerald-900/30 text-emerald-300 border-emerald-500/30'
                        }`}>
                        {opt.type.toUpperCase()}
                      </span>
                      <span className="text-emerald-400 font-bold">{opt.price_estimate}</span>
                    </div>
                    <h4 className="text-white font-bold">{opt.name}</h4>
                    <p className="text-xs text-slate-400 mb-2">{opt.provider}</p>
                    <p className="text-sm text-slate-300 mb-3">{opt.details}</p>
                    {opt.features && (
                      <div className="flex flex-wrap gap-1 mb-3">
                        {opt.features.slice(0, 2).map((feat, i) => (
                          <span key={i} className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded">
                            {feat}
                          </span>
                        ))}
                      </div>
                    )}
                    <button className="w-full py-2 bg-slate-800 hover:bg-blue-600 text-white text-sm rounded-lg transition-colors">
                      Book Now
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Budget Widget */}
          <div className="glass-card p-6 rounded-2xl border border-white/10">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <span>💵</span> Budget Breakdown
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-end mb-2">
                <span className="text-slate-400 text-sm">Estimated Total</span>
                <div className="text-right">
                  <div className="text-2xl font-bold text-emerald-400">
                    ${(itinerary.budget?.estimated_total || 0).toLocaleString()}
                  </div>
                  <div className="text-xs text-slate-500">
                    / ${(itinerary.budget?.total_budget || 0).toLocaleString()} Budget
                  </div>
                </div>
              </div>
              {/* Progress Bar */}
              <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-emerald-500 to-emerald-300"
                  style={{
                    width: `${Math.min(100, ((itinerary.budget?.estimated_total || 0) / (itinerary.budget?.total_budget || 1)) * 100)}%`
                  }}
                ></div>
              </div>

              <div className="space-y-3 pt-4 border-t border-slate-700/50">
                {itinerary.budget?.breakdown.map((item, idx) => (
                  <div key={idx} className="flex justify-between text-sm">
                    <span className="text-slate-300">{item.category}</span>
                    <span className="font-mono text-slate-400">${item.estimated_cost}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Packing List Widget */}
          <div className="glass-card p-6 rounded-2xl border border-white/10">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <span>🎒</span> Smart Packing
            </h3>
            <ul className="space-y-3">
              {itinerary.packing_list.map((item, i) => (
                <li key={i} className="flex items-start gap-3 group">
                  <div className="mt-1 w-4 h-4 rounded border border-purple-500/50 group-hover:bg-purple-500/20 transition-colors"></div>
                  <span className="text-slate-300 text-sm group-hover:text-white transition-colors">{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Warnings Widget (if any) */}
          {(itinerary.validation?.length > 0 || itinerary.warnings?.length > 0) && (
            <div className="bg-orange-500/10 border border-orange-500/20 p-6 rounded-2xl">
              <h3 className="text-xl font-bold text-orange-400 mb-3 flex items-center gap-2">
                <span>⚠️</span> Travel Notes
              </h3>
              <ul className="list-disc pl-5 space-y-2">
                {itinerary.validation?.map((v, i) => (
                  <li key={`val-${i}`} className="text-orange-200/80 text-sm">
                    {v.details}
                  </li>
                ))}
                {itinerary.warnings?.map((w, i) => (
                  <li key={`warn-${i}`} className="text-orange-200/80 text-sm">
                    {w}
                  </li>
                ))}
              </ul>
            </div>
          )}

        </div>
      </div>

      {/* Edit Modal */}
      {editingBlock && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/90 backdrop-blur-md transition-opacity"
            onClick={() => setEditingBlock(null)}
          />
          <div className={`relative bg-slate-900 border border-slate-600 rounded-2xl w-full ${suggestedBlock ? 'max-w-4xl' : 'max-w-lg'} p-6 shadow-2xl shadow-emerald-900/20 transition-all duration-300`}>
            <h3 className="text-2xl font-bold text-white mb-4">
              {suggestedBlock ? "Review & Edit" : "Edit Itinerary Item"}
            </h3>

            {!suggestedBlock ? (
              // Step 1: Instruction
              <>
                <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700 mb-4">
                  <p className="text-sm font-medium text-purple-300 mb-1">{editingBlock.block.title}</p>
                  <p className="text-xs text-slate-400 line-clamp-2">{editingBlock.block.description}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">What would you like to change?</label>
                  <textarea
                    value={editInstruction}
                    onChange={(e) => setEditInstruction(e.target.value)}
                    placeholder="e.g., 'Make this a vegetarian restaurant' or 'Change to a museum nearby'"
                    className="w-full h-24 bg-slate-950 border border-slate-700 rounded-xl p-3 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none placeholder:text-slate-600"
                    autoFocus
                  />
                </div>
                <div className="flex gap-3 justify-end pt-4">
                  <button onClick={() => setEditingBlock(null)} className="px-4 py-2 rounded-lg text-slate-300 hover:bg-slate-800 transition-colors">Cancel</button>
                  <button
                    onClick={submitEdit}
                    disabled={isEditing || !editInstruction.trim()}
                    className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium disabled:opacity-50 flex items-center gap-2"
                  >
                    {isEditing ? <span className="animate-spin">⏳</span> : <span>✨</span>}
                    {isEditing ? "Generating..." : "Generate Suggestion"}
                  </button>
                </div>
              </>
            ) : (
              // Step 2: Compare & Edit
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Current Block (Read Only) */}
                  <div className="space-y-3 opacity-60 pointer-events-none">
                    <h4 className="text-sm uppercase tracking-wide text-slate-500 font-bold border-b border-slate-700 pb-2">Original</h4>
                    <div>
                      <label className="text-xs text-slate-500">Title</label>
                      <div className="bg-slate-800 p-2 rounded border border-slate-700 text-slate-300 text-sm">{editingBlock.block.title}</div>
                    </div>
                    <div>
                      <label className="text-xs text-slate-500">Description</label>
                      <div className="bg-slate-800 p-2 rounded border border-slate-700 text-slate-400 text-xs h-20 overflow-y-auto">{editingBlock.block.description}</div>
                    </div>
                  </div>

                  {/* Suggested Block (Editable) */}
                  <div className="space-y-3">
                    <h4 className="text-sm uppercase tracking-wide text-emerald-500 font-bold border-b border-emerald-500/30 pb-2 flex items-center gap-2">
                      <span>✨</span> Suggestion
                    </h4>
                    <div>
                      <label className="text-xs text-emerald-400/80">Title</label>
                      <input
                        value={suggestedBlock.title}
                        onChange={(e) => setSuggestedBlock({ ...suggestedBlock, title: e.target.value })}
                        className="w-full bg-slate-950 p-2 rounded border border-emerald-500/50 text-white text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-emerald-400/80">Description</label>
                      <textarea
                        value={suggestedBlock.description}
                        onChange={(e) => setSuggestedBlock({ ...suggestedBlock, description: e.target.value })}
                        className="w-full bg-slate-950 p-2 rounded border border-emerald-500/50 text-slate-300 text-xs h-20 focus:outline-none focus:ring-1 focus:ring-emerald-500 resize-none"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="text-xs text-emerald-400/80">Start</label>
                        <input value={suggestedBlock.start_time} onChange={(e) => setSuggestedBlock({ ...suggestedBlock, start_time: e.target.value })} className="w-full bg-slate-950 p-2 rounded border border-emerald-500/50 text-white text-xs" />
                      </div>
                      <div>
                        <label className="text-xs text-emerald-400/80">End</label>
                        <input value={suggestedBlock.end_time} onChange={(e) => setSuggestedBlock({ ...suggestedBlock, end_time: e.target.value })} className="w-full bg-slate-950 p-2 rounded border border-emerald-500/50 text-white text-xs" />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3 justify-end pt-4 border-t border-slate-700/50">
                  <button onClick={() => setEditingBlock(null)} className="px-4 py-2 rounded-lg text-slate-300 hover:bg-slate-800 transition-colors">Discard</button>
                  <button
                    onClick={handleSave}
                    disabled={isSaving}
                    className="px-6 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold shadow-lg shadow-emerald-900/20 disabled:opacity-50 flex items-center gap-2"
                  >
                    {isSaving ? <span className="animate-spin">⏳</span> : <span>💾</span>}
                    {isSaving ? "Saving..." : "Accept & Save"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

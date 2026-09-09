import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, Switch, TouchableOpacity, Modal, Dimensions } from 'react-native';
import { BarChart } from 'react-native-chart-kit';
import { Centrifuge } from 'centrifuge';
import axios from 'axios';

const screenWidth = Dimensions.get("window").width;

export default function WorkspaceScreen() {
  const [isAvailable, setIsAvailable] = useState(false);
  const [incomingCall, setIncomingCall] = useState(null);
  const [stats, setStats] = useState({ calls_today: 0, calls_this_week: [0,0,0,0,0,0,0] });

  const data = {
    labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    datasets: [
      {
        data: stats.calls_this_week
      }
    ]
  };

  useEffect(() => {
    // Connect to Django backend to get initial state
    // We would normally pass JWT token here. We'll mock the fetch for the demo if backend isn't running with auth.
    const fetchState = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/me/state/', {
          // headers: { Authorization: `Bearer ${token}` }
        });
        setIsAvailable(response.data.state === 'AVAILABLE');
        if (response.data.analytics) setStats(response.data.analytics);
      } catch (err) {
        console.log("Could not fetch state (backend might be down or requires auth). Using mock stats.");
        setStats({ calls_today: 12, calls_this_week: [10, 15, 8, 12, 5, 2, 0] });
      }
    };
    fetchState();

    // Centrifugo connection
    // Note: To test this end-to-end, you need a Centrifugo server running on ws://localhost:8000/connection/websocket
    // Because we might not have it running in the background, we'll setup the client but also expose a mock method.
    const centrifuge = new Centrifuge('ws://localhost:8000/connection/websocket');
    
    // We would subscribe to the agent's personal channel (e.g., agent_1)
    const sub = centrifuge.newSubscription('agent_1');
    sub.on('publication', function(ctx) {
        const data = ctx.data;
        if (data.type === 'incoming_transfer') {
            setIncomingCall({ caller: data.caller_id, summary: data.summary });
        }
    });
    sub.subscribe();
    centrifuge.connect();

    // Expose mock for easy testing in browser console: window.simulateIncomingCall('Bob', 'Billing issue')
    if (typeof window !== 'undefined') {
      window.simulateIncomingCall = (caller, summary) => {
        setIncomingCall({ caller, summary });
      };
    }

    return () => {
      centrifuge.disconnect();
    };
  }, []);

  const handleStateChange = async (value) => {
    setIsAvailable(value);
    const newState = value ? 'AVAILABLE' : 'OFFLINE';
    try {
      await axios.patch('http://localhost:8000/api/me/state/', { state: newState });
    } catch (e) {
      console.log("Mock state update locally since backend is unreachable/unauth");
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Agent Workspace</Text>
        <View style={styles.statusContainer}>
          <Text style={styles.statusText}>{isAvailable ? 'AVAILABLE' : 'OFFLINE'}</Text>
          <Switch value={isAvailable} onValueChange={handleStateChange} />
        </View>
      </View>

      <View style={styles.dashboard}>
        <Text style={styles.chartTitle}>Calls Handled This Week</Text>
        <BarChart
          data={data}
          width={Math.min(screenWidth - 40, 600)}
          height={220}
          yAxisLabel=""
          chartConfig={chartConfig}
          verticalLabelRotation={0}
          style={styles.chart}
        />
        <Text style={styles.todayStats}>Calls Today: {stats.calls_today}</Text>
      </View>

      {/* Incoming Call Modal */}
      <Modal visible={!!incomingCall} transparent={true} animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.callCard}>
            <Text style={styles.callHeader}>Incoming Transfer</Text>
            <Text style={styles.callerId}>From: {incomingCall?.caller}</Text>
            
            <View style={styles.summaryBox}>
              <Text style={styles.summaryLabel}>AI Conversation Summary:</Text>
              <Text style={styles.summaryText}>{incomingCall?.summary}</Text>
            </View>

            <View style={styles.buttonRow}>
              <TouchableOpacity 
                style={[styles.button, styles.acceptBtn]} 
                onPress={() => setIncomingCall(null)}
              >
                <Text style={styles.buttonText}>Accept</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.button, styles.rejectBtn]} 
                onPress={() => setIncomingCall(null)}
              >
                <Text style={styles.buttonText}>Reject</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const chartConfig = {
  backgroundGradientFrom: "#ffffff",
  backgroundGradientTo: "#ffffff",
  color: (opacity = 1) => `rgba(0, 122, 255, ${opacity})`,
  labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
  barPercentage: 0.5,
  fillShadowGradientOpacity: 1,
  decimalPlaces: 0,
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F7FA', // Light style
    padding: 20,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 30,
    backgroundColor: '#FFF',
    padding: 15,
    borderRadius: 10,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 5,
    elevation: 2,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusText: {
    marginRight: 10,
    fontWeight: '600',
    color: '#666',
  },
  dashboard: {
    backgroundColor: '#FFF',
    padding: 20,
    borderRadius: 10,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 5,
    elevation: 2,
  },
  chartTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 20,
    color: '#444',
  },
  chart: {
    borderRadius: 10,
    paddingRight: 30,
  },
  todayStats: {
    marginTop: 15,
    fontSize: 16,
    color: '#666',
    fontWeight: '500',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  callCard: {
    width: Math.min(screenWidth - 40, 400),
    backgroundColor: '#FFF',
    padding: 25,
    borderRadius: 15,
    shadowColor: '#000',
    shadowOpacity: 0.2,
    shadowRadius: 10,
    elevation: 5,
  },
  callHeader: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#E53E3E',
    marginBottom: 10,
    textAlign: 'center',
  },
  callerId: {
    fontSize: 16,
    color: '#555',
    marginBottom: 20,
    textAlign: 'center',
  },
  summaryBox: {
    backgroundColor: '#FFF5F5',
    padding: 15,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#E53E3E',
    marginBottom: 25,
  },
  summaryLabel: {
    fontWeight: 'bold',
    color: '#C53030',
    marginBottom: 5,
  },
  summaryText: {
    fontSize: 15,
    color: '#2D3748',
    lineHeight: 22,
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  button: {
    flex: 1,
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  acceptBtn: {
    backgroundColor: '#48BB78',
    marginRight: 10,
  },
  rejectBtn: {
    backgroundColor: '#A0AEC0',
    marginLeft: 10,
  },
  buttonText: {
    color: '#FFF',
    fontWeight: 'bold',
    fontSize: 16,
  }
});

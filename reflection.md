# PawPal+ Project Reflection

## 1. System Design

Three core actions a user should be able to perform are:
    1. adding a pet
    2. Scheduling meal times for pet
    3. Let the user see each day's schedule/task

Class/Object: Owner
    Attributes:
        - Owner name
        - Owner available times
        - Owner preferences
        - Owner pets
    Methods:
        - add pet()
        - update availability() <-- In case owner wants to change available time

Class/Object: Pet
    Attributes:
        - Pet name
        - Pet species
        - pet tasks <-- Last of tasks(the object)/assignments the pet has to do 
    Methods:
        - add task()
        - remove task()  

Class/Object: CareTask
    Attributes:
        - Task name <-- like evening walk or lunch time
        - Task category(Grooming, feeding, medical, etc.)
        - Task duration <-- how long a task takes
        - Task priority(1. Critical/very important to 3. Optional/not essential)
    Methods:
        - update priority()
        - update duration()

Class/Object: Scheduler
    Attributes:
        - Owner object <-- Need Owner's available times and other information
        - date
        - all tasks <-- a list with tasks of all pets(unsorted)
        - scheduled tasks <-- a list where all Scheduled tasks from scheduleer goes into
        - unscheduled tasks <-- a list where all Unscheduled tasks from scheduler goes into
        - reasoning log <-- a list which holds all generate reasoning results together
    Methods:
        - gather all tasks(): Take every CareTask from the owner's Pet objects and add that to all tasks 
        - build schedule(): First this method sorts the all tasks by priority, then task duration. Next it compares each sorted task against the user's availability time, and sends the task into Sceduled or Unscheduled tasks list based on that. Then it creates a log on why the task got sent into Scheduled or Unscheduled list based on User's availability time and adds that to the resoning log list. 
        - send plan(): Sends plan in proper format to streamlit 
    
**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?



![alt text](image.png)